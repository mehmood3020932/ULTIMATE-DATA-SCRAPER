// internal/browser/pool.go
// Browser instance pool

package browser

import (
	"context"
	"sync"

	"github.com/playwright-community/playwright-go"
)

type Pool struct {
	maxSize   int
	instances chan *playwright.BrowserContext
	mu        sync.Mutex
	pw        *playwright.Playwright
	browser   playwright.Browser
}

func NewPool(maxSize int) *Pool {
	return &Pool{
		maxSize:   maxSize,
		instances: make(chan *playwright.BrowserContext, maxSize),
	}
}

func (p *Pool) Initialize() error {
	pw, err := playwright.Run()
	if err != nil {
		return err
	}
	p.pw = pw
	
	browser, err := pw.Chromium.Launch()
	if err != nil {
		return err
	}
	p.browser = browser
	
	// Pre-warm pool
	for i := 0; i < p.maxSize; i++ {
		ctx, err := browser.NewContext()
		if err != nil {
			return err
		}
		p.instances <- ctx
	}
	
	return nil
}

func (p *Pool) Acquire(ctx context.Context) (*playwright.BrowserContext, error) {
	select {
	case instance := <-p.instances:
		return instance, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

func (p *Pool) Release(instance *playwright.BrowserContext) {
	select {
	case p.instances <- instance:
	default:
		// Pool full, close instance
		instance.Close()
	}
}

func (p *Pool) Close() {
	close(p.instances)
	for instance := range p.instances {
		instance.Close()
	}
	p.browser.Close()
	p.pw.Stop()
}