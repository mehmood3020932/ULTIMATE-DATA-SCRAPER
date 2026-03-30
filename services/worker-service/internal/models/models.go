// internal/models/models.go
// Shared data models

package models

import "time"

type Job struct {
	ID           string                 `json:"id"`
	UserID       string                 `json:"user_id"`
	URL          string                 `json:"url"`
	Instructions string                 `json:"instructions"`
	Config       JobConfig              `json:"config"`
	CreatedAt    time.Time              `json:"created_at"`
}

type JobConfig struct {
	MaxDepth          int    `json:"max_depth"`
	MaxPages          int    `json:"max_pages"`
	TimeoutSeconds    int    `json:"timeout_seconds"`
	FollowPagination  bool   `json:"follow_pagination"`
	JavaScriptEnabled bool   `json:"javascript_enabled"`
	UserAgent         string `json:"user_agent"`
	ProxyCountry      string `json:"proxy_country"`
	WaitForSelector   string `json:"wait_for_selector"`
}

type ScrapedPage struct {
	URL       string            `json:"url"`
	HTML      string            `json:"html"`
	Title     string            `json:"title"`
	Links     []string          `json:"links"`
	Metadata  map[string]string `json:"metadata"`
	Timestamp time.Time         `json:"timestamp"`
}