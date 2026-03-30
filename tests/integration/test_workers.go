// tests/integration/test_workers.go
package integration

import (
	"net/http"
	"testing"
)

func TestWorkerHealth(t *testing.T) {
	resp, err := http.Get("http://localhost:8080/health")
	if err != nil {
		t.Fatalf("Failed to reach worker: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}
}

func TestWorkerReady(t *testing.T) {
	resp, err := http.Get("http://localhost:8080/ready")
	if err != nil {
		t.Fatalf("Failed to reach worker: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}
}