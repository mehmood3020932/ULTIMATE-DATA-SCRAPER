// services/worker-service/internal/scraper/scraper.go
// Core scraping logic

package scraper

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/aiscraping/worker-service/internal/config"
	"github.com/aiscraping/worker-service/pkg/logger"
	"github.com/cenkalti/backoff/v4"
	"github.com/segmentio/kafka-go"
)

// Job represents a scraping job
type Job struct {
	ID            string                 `json:"id"`
	UserID        string                 `json:"user_id"`
	URL           string                 `json:"url"`
	Instructions  string                 `json:"instructions"`
	Config        JobConfig              `json:"config"`
	CreatedAt     time.Time              `json:"created_at"`
}

type JobConfig struct {
	MaxDepth          int    `json:"max_depth"`
	MaxPages          int    `json:"max_pages"`
	TimeoutSeconds    int    `json:"timeout_seconds"`
	FollowPagination  bool   `json:"follow_pagination"`
	JavaScriptEnabled bool   `json:"javascript_enabled"`
	UserAgent         string `json:"user_agent"`
	ProxyCountry      string `json:"proxy_country"`
	WaitForSelector   string `json:"wait_for_selector"`
}

// Result represents scraping result
type Result struct {
	JobID         string                 `json:"job_id"`
	Success       bool                   `json:"success"`
	HTML          string                 `json:"html,omitempty"`
	Title         string                 `json:"title,omitempty"`
	Links         []string               `json:"links,omitempty"`
	Data          map[string]interface{} `json:"data,omitempty"`
	Error         string                 `json:"error,omitempty"`
	PageCount     int                    `json:"page_count"`
	DurationMs    int64                  `json:"duration_ms"`
	Timestamp     time.Time              `json:"timestamp"`
}

// Pool manages scraper workers
type Pool struct {
	config    *config.Config
	logger    *logger.Logger
	workers   int
	semaphore chan struct{}
	browser   *BrowserManager
	mu        sync.RWMutex
	healthy   bool
}

// NewPool creates new scraper pool
func NewPool(cfg *config.Config, log *logger.Logger) *Pool {
	return &Pool{
		config:    cfg,
		logger:    log,
		workers:   cfg.PlaywrightWorkers,
		semaphore: make(chan struct{}, cfg.PlaywrightWorkers),
		browser:   NewBrowserManager(cfg, log),
		healthy:   true,
	}
}

// Start initializes the pool
func (p *Pool) Start() error {
	if err := p.browser.Initialize(); err != nil {
		return fmt.Errorf("failed to initialize browser: %w", err)
	}
	p.healthy = true
	return nil
}

// Close shuts down the pool
func (p *Pool) Close() {
	p.browser.Close()
	p.healthy = false
}

// IsHealthy returns health status
func (p *Pool) IsHealthy() bool {
	return p.healthy
}

// ExecuteJob executes a scraping job with retry logic
func (p *Pool) ExecuteJob(ctx context.Context, job *Job) (*Result, error) {
	// Acquire semaphore
	select {
	case p.semaphore <- struct{}{}:
		defer func() { <-p.semaphore }()
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	startTime := time.Now()
	
	result := &Result{
		JobID:     job.ID,
		Timestamp: time.Now().UTC(),
	}

	// Execute with exponential backoff
	operation := func() error {
		return p.executeWithBrowser(ctx, job, result)
	}

	notify := func(err error, duration time.Duration) {
		p.logger.Warn("Retrying job after error",
			"job_id", job.ID,
			"error", err,
			"delay", duration,
		)
	}

	b := backoff.NewExponentialBackOff()
	b.MaxElapsedTime = time.Duration(job.Config.TimeoutSeconds) * time.Second

	if err := backoff.RetryNotify(operation, b, notify); err != nil {
		result.Success = false
		result.Error = err.Error()
		result.DurationMs = time.Since(startTime).Milliseconds()
		return result, err
	}

	result.Success = true
	result.DurationMs = time.Since(startTime).Milliseconds()
	return result, nil
}

func (p *Pool) executeWithBrowser(ctx context.Context, job *Job, result *Result) error {
	page, err := p.browser.NewPage(ctx, job.Config)
	if err != nil {
		return fmt.Errorf("failed to create page: %w", err)
	}
	defer page.Close()

	// Navigate to URL
	if err := page.Navigate(ctx, job.URL); err != nil {
		return fmt.Errorf("navigation failed: %w", err)
	}

	// Wait for selector if specified
	if job.Config.WaitForSelector != "" {
		if err := page.WaitForSelector(ctx, job.Config.WaitForSelector); err != nil {
			return fmt.Errorf("wait for selector failed: %w", err)
		}
	}

	// Extract content
	content, err := page.GetContent(ctx)
	if err != nil {
		return fmt.Errorf("content extraction failed: %w", err)
	}

	result.HTML = content
	result.Title = page.Title()
	result.PageCount = 1

	// Extract links if following pagination
	if job.Config.FollowPagination {
		links, err := page.GetLinks(ctx)
		if err == nil {
			result.Links = links
		}
	}

	return nil
}