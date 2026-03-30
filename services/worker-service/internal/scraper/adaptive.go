// internal/scraper/adaptive.go
// Adaptive scraping logic

package scraper

import (
	"context"
	"time"
)

// AdaptiveScraper adjusts strategy based on site behavior
type AdaptiveScraper struct {
	baseDelay    time.Duration
	currentDelay time.Duration
	successCount int
	failCount    int
}

func NewAdaptiveScraper() *AdaptiveScraper {
	return &AdaptiveScraper{
		baseDelay:    1 * time.Second,
		currentDelay: 1 * time.Second,
	}
}

func (a *AdaptiveScraper) GetDelay() time.Duration {
	return a.currentDelay
}

func (a *AdaptiveScraper) RecordSuccess() {
	a.successCount++
	// Gradually reduce delay on success
	if a.successCount > 10 && a.currentDelay > a.baseDelay {
		a.currentDelay -= 100 * time.Millisecond
	}
	a.failCount = 0
}

func (a *AdaptiveScraper) RecordFailure() {
	a.failCount++
	a.successCount = 0
	// Exponential backoff on failure
	a.currentDelay *= 2
	if a.currentDelay > 30*time.Second {
		a.currentDelay = 30 * time.Second
	}
}

func (a *AdaptiveScraper) Wait(ctx context.Context) error {
	timer := time.NewTimer(a.currentDelay)
	select {
	case <-ctx.Done():
		timer.Stop()
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}