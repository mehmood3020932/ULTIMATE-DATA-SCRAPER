// pkg/retry/retry.go
// Retry logic with backoff

package retry

import (
	"context"
	"time"
)

type Config struct {
	MaxRetries  int
	BaseDelay   time.Duration
	MaxDelay    time.Duration
	Multiplier  float64
}

func DefaultConfig() *Config {
	return &Config{
		MaxRetries: 3,
		BaseDelay:  1 * time.Second,
		MaxDelay:   30 * time.Second,
		Multiplier: 2.0,
	}
}

func Do(ctx context.Context, operation func() error, config *Config) error {
	if config == nil {
		config = DefaultConfig()
	}
	
	var err error
	delay := config.BaseDelay
	
	for attempt := 0; attempt <= config.MaxRetries; attempt++ {
		err = operation()
		if err == nil {
			return nil
		}
		
		if attempt == config.MaxRetries {
			break
		}
		
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(delay):
			delay = time.Duration(float64(delay) * config.Multiplier)
			if delay > config.MaxDelay {
				delay = config.MaxDelay
			}
		}
	}
	
	return err
}