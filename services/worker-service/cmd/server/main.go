// cmd/server/main.go
// Worker Service Entry Point - High-performance scraping with Playwright

package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"worker-service/internal/config"
	"worker-service/internal/queue"
	"worker-service/internal/scraper"
	"worker-service/pkg/logger"

	"github.com/gin-gonic/gin"
	"github.com/playwright-community/playwright-go"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/redis/go-redis/v9"
)

func main() {
	// Initialize logger
	log := logger.New()

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatal("Failed to load config: ", err)
	}

	// Initialize Playwright
	if err := playwright.Install(); err != nil {
		log.Fatal("Failed to install Playwright browsers: ", err)
	}

	pw, err := playwright.Run()
	if err != nil {
		log.Fatal("Failed to start Playwright: ", err)
	}
	defer pw.Stop()

	// Launch browser headless
	browser, err := pw.Chromium.Launch(playwright.BrowserTypeLaunchOptions{
		Headless: playwright.Bool(true),
		Args: []string{
			"--disable-dev-shm-usage",
			"--no-sandbox",
			"--disable-gpu",
			"--disable-setuid-sandbox",
		},
	})
	if err != nil {
		log.Fatal("Failed to launch browser: ", err)
	}
	defer browser.Close()

	log.Info("Playwright browser launched successfully")

	// Initialize Redis client
	redisClient := initRedis(cfg)
	defer redisClient.Close()

	// Initialize scraper pool with browser instance
	scraperPool := scraper.NewPoolWithBrowser(cfg, log, browser)
	defer scraperPool.Close()

	// Initialize queue consumer
	consumer := queue.NewConsumer(cfg, redisClient, scraperPool, log)

	// Setup HTTP server with Gin
	router := gin.New()
	router.Use(gin.Recovery())

	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"service":   "worker-service",
			"timestamp": time.Now().UTC(),
		})
	})

	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	router.GET("/ready", func(c *gin.Context) {
		if scraperPool.IsHealthy() {
			c.JSON(http.StatusOK, gin.H{"status": "ready"})
		} else {
			c.JSON(http.StatusServiceUnavailable, gin.H{"status": "not_ready"})
		}
	})

	srv := &http.Server{
		Addr:    ":" + cfg.Port,
		Handler: router,
	}

	// Start consumer in background
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		if err := consumer.Start(ctx); err != nil {
			log.Error("Consumer error: ", err)
		}
	}()

	// Start HTTP server
	go func() {
		log.Info("Starting server on port ", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("Server failed: ", err)
		}
	}()

	// Wait for OS signals to shut down
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("Shutting down gracefully...")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Error("Server forced to shutdown: ", err)
	}

	cancel() // Stop consumer

	log.Info("Server exited")
}

// initRedis returns a connected Redis client
func initRedis(cfg *config.Config) *redis.Client {
	rdb := redis.NewClient(&redis.Options{
		Addr:     cfg.RedisAddr,
		Password: cfg.RedisPassword,
		DB:       cfg.RedisDB,
	})
	return rdb
}