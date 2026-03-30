// internal/browser/stealth.go
// Stealth mode to avoid detection

package browser

import (
	"github.com/playwright-community/playwright-go"
)

type StealthConfig struct {
	UserAgent       string
	Viewport        playwright.ViewportSize
	Locale          string
	Timezone        string
	WebGLVendor     string
	WebGLRenderer   string
}

func DefaultStealthConfig() *StealthConfig {
	return &StealthConfig{
		UserAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
		Viewport: playwright.ViewportSize{
			Width:  1920,
			Height: 1080,
		},
		Locale:        "en-US",
		Timezone:      "America/New_York",
		WebGLVendor:   "Intel Inc.",
		WebGLRenderer: "Intel Iris OpenGL Engine",
	}
}

func ApplyStealthScripts(page playwright.Page) error {
	// Inject scripts to hide automation indicators
	scripts := []string{
		// Hide webdriver
		`Object.defineProperty(navigator, 'webdriver', {get: () => undefined})`,
		// Hide plugins length
		`Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})`,
		// Hide languages
		`Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})`,
		// Override permissions
		`const originalQuery = window.navigator.permissions.query;
		window.navigator.permissions.query = (parameters) => (
			parameters.name === 'notifications' ?
			Promise.resolve({ state: Notification.permission }) :
			originalQuery(parameters)
		)`,
	}
	
	for _, script := range scripts {
		_, err := page.Evaluate(script)
		if err != nil {
			return err
		}
	}
	
	return nil
}