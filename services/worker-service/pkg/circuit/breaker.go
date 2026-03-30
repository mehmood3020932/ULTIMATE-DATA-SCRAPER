// pkg/circuit/breaker.go
// Circuit breaker pattern

package circuit

import (
	"sync"
	"time"
)

type State int

const (
	StateClosed State = iota
	StateOpen
	StateHalfOpen
)

type Breaker struct {
	failureThreshold int
	resetTimeout     time.Duration
	state            State
	failures         int
	lastFailureTime  time.Time
	mu               sync.Mutex
}

func NewBreaker(failureThreshold int, resetTimeout time.Duration) *Breaker {
	return &Breaker{
		failureThreshold: failureThreshold,
		resetTimeout:     resetTimeout,
		state:            StateClosed,
	}
}

func (b *Breaker) Call(operation func() error) error {
	b.mu.Lock()
	state := b.state
	b.mu.Unlock()
	
	if state == StateOpen {
		if time.Since(b.lastFailureTime) > b.resetTimeout {
			b.mu.Lock()
			b.state = StateHalfOpen
			b.mu.Unlock()
		} else {
			return ErrCircuitOpen
		}
	}
	
	err := operation()
	b.recordResult(err)
	return err
}

func (b *Breaker) recordResult(err error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	
	if err == nil {
		b.failures = 0
		b.state = StateClosed
		return
	}
	
	b.failures++
	b.lastFailureTime = time.Now()
	
	if b.failures >= b.failureThreshold {
		b.state = StateOpen
	}
}

var ErrCircuitOpen = NewBreakerError("circuit breaker is open")

type BreakerError struct {
	msg string
}

func NewBreakerError(msg string) error {
	return &BreakerError{msg: msg}
}

func (e *BreakerError) Error() string {
	return e.msg
}