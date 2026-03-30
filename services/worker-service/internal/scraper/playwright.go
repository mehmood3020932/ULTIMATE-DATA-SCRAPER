// services/worker-service/internal/scraper/playwright.go
// Playwright browser management

package scraper

import (
	"context"
	"fmt"
	"sync"

	"github.com/aiscraping/worker-service/internal/config"
	"github.com/aiscraping/worker-service/pkg/logger"
	"github.com/playwright-community/playwright-go"
)

// BrowserManager manages Playwright browser instances
type BrowserManager struct {
	config   *config.Config
	logger   *logger.Logger
	pw       *playwright.Playwright
	browser  playwright.Browser
	mu       sync.RWMutex
}

// NewBrowserManager creates new browser manager
func NewBrowserManager(cfg *config.Config, log *logger.Logger) *BrowserManager {
	return &BrowserManager{
		config: cfg,
		logger: log,
	}
}

// Initialize sets up Playwright
func (bm *BrowserManager) Initialize() error {
	bm.mu.Lock()
	defer bm.mu.Unlock()

	if err := playwright.Install(); err != nil {
		return fmt.Errorf("could not install Playwright: %w", err)
	}

	pw, err := playwright.Run()
	if err != nil {
		return fmt.Errorf("could not start Playwright: %w", err)
	}
	bm.pw = pw

	browser, err := pw.Chromium.Launch(playwright.BrowserTypeLaunchOptions{
		Headless: playwright.Bool(true),
		Args: []string{
			"--disable-dev-shm-usage",
			"--disable-gpu",
			"--no-sandbox",
			"--disable-setuid-sandbox",
			"--disable-web-security",
			"--disable-features=IsolateOrigins,site-per-process",
		},
	})
	if err != nil {
		return fmt.Errorf("could not launch browser: %w", err)
	}
	bm.browser = browser

	bm.logger.Info("Browser manager initialized")
	return nil
}

// Close shuts down browser
func (bm *BrowserManager) Close() {
	bm.mu.Lock()
	defer bm.mu.Unlock()

	if bm.browser != nil {
		bm.browser.Close()
	}
	if bm.pw != nil {
		bm.pw.Stop()
	}
}

// NewPage creates new browser page
func (bm *BrowserManager) NewPage(ctx context.Context, config JobConfig) (*Page, error) {
	bm.mu.RLock()
	defer bm.mu.RUnlock()

	if bm.browser == nil {
		return nil, fmt.Errorf("browser not initialized")
	}

	contextOptions := playwright.BrowserNewContextOptions{
		UserAgent: playwright.String(config.UserAgent),
		Viewport: &playwright.ViewportSize{
			Width:  1920,
			Height: 1080,
		},
		Locale:        playwright.String("en-US"),
		TimezoneId:    playwright.String("America/New_York"),
		Permissions:   []string{"notifications"},
		JavaScriptEnabled: playwright.Bool(config.JavaScriptEnabled),
	}

	if config.ProxyCountry != "" {
		// Configure proxy based on country
		contextOptions.Proxy = &playwright.Proxy{
			Server:   bm.config.ProxyURL,
			Username: playwright.String("user"),
			Password: playwright.String("pass"),
		}
	}

	browserContext, err := bm.browser.NewContext(contextOptions)
	if err != nil {
		return nil, fmt.Errorf("could not create context: %w", err)
	}

	page, err := browserContext.NewPage()
	if err != nil {
		browserContext.Close()
		return nil, fmt.Errorf("could not create page: %w", err)
	}

	return &Page{
		page:    page,
		context: browserContext,
		logger:  bm.logger,
	}, nil
}

// Page represents a browser page
type Page struct {
	page    playwright.Page
	context playwright.BrowserContext
	logger  *logger.Logger
	title   string
}

// Navigate to URL
func (p *Page) Navigate(ctx context.Context, url string) error {
	response, err := p.page.Goto(url, playwright.PageGotoOptions{
		WaitUntil: playwright.WaitUntilStateNetworkidle,
		Timeout:   playwright.Float(30000),
	})
	if err != nil {
		return err
	}
	if response == nil {
		return fmt.Errorf("no response received")
	}
	if response.Status() >= 400 {
		return fmt.Errorf("HTTP error: %d", response.Status())
	}
	return nil
}

// WaitForSelector waits for element
func (p *Page) WaitForSelector(ctx context.Context, selector string) error {
	return p.page.WaitForSelector(selector, playwright.PageWaitForSelectorOptions{
		Timeout: playwright.Float(10000),
		State:   playwright.WaitForSelectorStateVisible,
	})
}

// GetContent returns page HTML
func (p *Page) GetContent(ctx context.Context) (string, error) {
	return p.page.Content()
}

// Title returns page title
func (p *Page) Title() string {
	title, _ := p.page.Title()
	return title
}

// GetLinks extracts all links
func (p *Page) GetLinks(ctx context.Context) ([]string, error) {
	links, err := p.page.Evaluate(`() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)`)
	if err != nil {
		return nil, err
	}

	var result []string
	if hrefs, ok := links.([]interface{}); ok {
		for _, href := range hrefs {
			if s, ok := href.(string); ok {
				result = append(result, s)
			}
		}
	}
	return result, nil
}

// Close closes page
func (p *Page) Close() {
	p.page.Close()
	p.context.Close()
}