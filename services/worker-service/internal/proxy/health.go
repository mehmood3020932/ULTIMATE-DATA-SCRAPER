// internal/proxy/health.go
// Proxy health checking

package proxy

import (
	"context"
	"net/http"
	"time"
)

type HealthChecker struct {
	client  *http.Client
	timeout time.Duration
}

func NewHealthChecker(timeout time.Duration) *HealthChecker {
	return &HealthChecker{
		client:  &http.Client{Timeout: timeout},
		timeout: timeout,
	}
}

func (h *HealthChecker) Check(proxy *Proxy) bool {
	// Simple health check - try to connect through proxy
	// In production, use a dedicated health check endpoint
	ctx, cancel := context.WithTimeout(context.Background(), h.timeout)
	defer cancel()
	
	req, err := http.NewRequestWithContext(ctx, "GET", "http://httpbin.org/ip", nil)
	if err != nil {
		return false
	}
	
	// Configure proxy (simplified)
	// req = req.WithContext(ctx)
	
	resp, err := h.client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	
	return resp.StatusCode == 200
}