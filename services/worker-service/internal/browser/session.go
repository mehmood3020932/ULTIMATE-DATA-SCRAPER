// internal/browser/session.go
// Browser session management

package browser

import (
	"context"
	"time"

	"github.com/playwright-community/playwright-go"
)

type Session struct {
	context    playwright.BrowserContext
	page       playwright.Page
	startedAt  time.Time
	lastUsedAt time.Time
}

func NewSession(context playwright.BrowserContext) (*Session, error) {
	page, err := context.NewPage()
	if err != nil {
		return nil, err
	}
	
	return &Session{
		context:    context,
		page:       page,
		startedAt:  time.Now(),
		lastUsedAt: time.Now(),
	}, nil
}

func (s *Session) Navigate(ctx context.Context, url string) error {
	_, err := s.page.Goto(url, playwright.PageGotoOptions{
		WaitUntil: playwright.WaitUntilStateNetworkidle,
		Timeout:   playwright.Float(30000),
	})
	s.lastUsedAt = time.Now()
	return err
}

func (s *Session) GetContent() (string, error) {
	s.lastUsedAt = time.Now()
	return s.page.Content()
}

func (s *Session) Close() error {
	return s.page.Close()
}