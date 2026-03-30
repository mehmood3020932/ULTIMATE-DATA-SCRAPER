// internal/proxy/rotator.go
// Proxy rotation strategies

package proxy

import (
	"sync"
)

type Rotator struct {
	manager  *Manager
	strategy string // round_robin, random, least_used
	mu       sync.Mutex
	index    int
}

func NewRotator(manager *Manager, strategy string) *Rotator {
	return &Rotator{
		manager:  manager,
		strategy: strategy,
		index:    0,
	}
}

func (r *Rotator) Next() *Proxy {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	switch r.strategy {
	case "round_robin":
		return r.roundRobin()
	case "random":
		return r.manager.GetProxy()
	default:
		return r.manager.GetProxy()
	}
}

func (r *Rotator) roundRobin() *Proxy {
	proxy := r.manager.proxies[r.index%len(r.manager.proxies)]
	r.index++
	return proxy
}