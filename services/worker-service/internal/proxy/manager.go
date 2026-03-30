// internal/proxy/manager.go
// Proxy management

package proxy

import (
	"math/rand"
	"sync"
)

type Proxy struct {
	URL      string
	Username string
	Password string
	Country  string
	Healthy  bool
}

type Manager struct {
	proxies []*Proxy
	mu      sync.RWMutex
	current int
}

func NewManager(proxyURLs []string) *Manager {
	proxies := make([]*Proxy, len(proxyURLs))
	for i, url := range proxyURLs {
		proxies[i] = &Proxy{URL: url, Healthy: true}
	}
	return &Manager{proxies: proxies}
}

func (m *Manager) GetProxy() *Proxy {
	m.mu.RLock()
	defer m.mu.RUnlock()
	
	healthy := make([]*Proxy, 0)
	for _, p := range m.proxies {
		if p.Healthy {
			healthy = append(healthy, p)
		}
	}
	
	if len(healthy) == 0 {
		return nil
	}
	
	return healthy[rand.Intn(len(healthy))]
}

func (m *Manager) MarkUnhealthy(proxy *Proxy) {
	m.mu.Lock()
	defer m.mu.Unlock()
	proxy.Healthy = false
}