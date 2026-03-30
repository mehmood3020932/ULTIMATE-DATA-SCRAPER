// services/worker-service/internal/config/config.go
// Configuration management

package config

import (
	"github.com/spf13/viper"
)

type Config struct {
	Port              string `mapstructure:"PORT"`
	Environment       string `mapstructure:"ENVIRONMENT"`
	LogLevel          string `mapstructure:"LOG_LEVEL"`
	
	// Redis
	RedisURL          string `mapstructure:"REDIS_URL"`
	RedisPoolSize     int    `mapstructure:"REDIS_POOL_SIZE"`
	
	// Kafka
	KafkaBrokers      string `mapstructure:"KAFKA_BROKERS"`
	KafkaGroupID      string `mapstructure:"KAFKA_GROUP_ID"`
	KafkaTopicJobs    string `mapstructure:"KAFKA_TOPIC_JOBS"`
	
	// Playwright
	PlaywrightWorkers int    `mapstructure:"PLAYWRIGHT_WORKERS"`
	BrowserTimeout    int    `mapstructure:"BROWSER_TIMEOUT"`
	
	// Proxy
	ProxyURL          string `mapstructure:"PROXY_URL"`
	ProxyRotation     bool   `mapstructure:"PROXY_ROTATION"`
	
	// Scraping
	MaxPagesPerJob    int    `mapstructure:"MAX_PAGES_PER_JOB"`
	DefaultTimeout    int    `mapstructure:"DEFAULT_TIMEOUT"`
}

func Load() (*Config, error) {
	viper.SetDefault("PORT", "8080")
	viper.SetDefault("ENVIRONMENT", "development")
	viper.SetDefault("LOG_LEVEL", "info")
	viper.SetDefault("REDIS_URL", "redis://localhost:6379/0")
	viper.SetDefault("REDIS_POOL_SIZE", "50")
	viper.SetDefault("KAFKA_BROKERS", "localhost:9092")
	viper.SetDefault("KAFKA_GROUP_ID", "worker-service")
	viper.SetDefault("KAFKA_TOPIC_JOBS", "scraping.jobs")
	viper.SetDefault("PLAYWRIGHT_WORKERS", "10")
	viper.SetDefault("BROWSER_TIMEOUT", "30")
	viper.SetDefault("MAX_PAGES_PER_JOB", "1000")
	viper.SetDefault("DEFAULT_TIMEOUT", "30")

	viper.AutomaticEnv()

	var cfg Config
	if err := viper.Unmarshal(&cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}