// services/worker-service/pkg/logger/logger.go
// Structured logging

package logger

import (
	"github.com/sirupsen/logrus"
)

// Logger wraps logrus
type Logger struct {
	*logrus.Logger
}

// New creates new logger
func New() *Logger {
	log := logrus.New()
	log.SetFormatter(&logrus.JSONFormatter{
		TimestampFormat: "2006-01-02T15:04:05.000Z07:00",
	})
	log.SetLevel(logrus.InfoLevel)
	return &Logger{log}
}

// WithField adds field to log entry
func (l *Logger) WithField(key string, value interface{}) *Logger {
	return &Logger{l.Logger.WithField(key, value).Logger}
}

// WithFields adds multiple fields
func (l *Logger) WithFields(fields map[string]interface{}) *Logger {
	return &Logger{l.Logger.WithFields(fields).Logger}
}