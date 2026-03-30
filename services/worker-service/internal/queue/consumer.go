// services/worker-service/internal/queue/consumer.go
// Kafka consumer for job processing

package queue

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/aiscraping/worker-service/internal/config"
	"github.com/aiscraping/worker-service/internal/scraper"
	"github.com/aiscraping/worker-service/pkg/logger"
	"github.com/redis/go-redis/v9"
	"github.com/segmentio/kafka-go"
)

// Consumer handles job consumption from Kafka
type Consumer struct {
	config      *config.Config
	redis       *redis.Client
	scraperPool *scraper.Pool
	logger      *logger.Logger
	reader      *kafka.Reader
}

// NewConsumer creates new consumer
func NewConsumer(
	cfg *config.Config,
	redisClient *redis.Client,
	scraperPool *scraper.Pool,
	log *logger.Logger,
) *Consumer {
	return &Consumer{
		config:      cfg,
		redis:       redisClient,
		scraperPool: scraperPool,
		logger:      log,
	}
}

// Start begins consuming messages
func (c *Consumer) Start(ctx context.Context) error {
	c.reader = kafka.NewReader(kafka.ReaderConfig{
		Brokers:     []string{c.config.KafkaBrokers},
		GroupID:     c.config.KafkaGroupID,
		Topic:       c.config.KafkaTopicJobs,
		MinBytes:    10e3, // 10KB
		MaxBytes:    10e6, // 10MB
		StartOffset: kafka.FirstOffset,
	})

	c.logger.Info("Kafka consumer started")

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		m, err := c.reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				return nil
			}
			c.logger.Error("Failed to read message: ", err)
			continue
		}

		var event struct {
			Event   string          `json:"event"`
			JobID   string          `json:"job_id"`
			JobData json.RawMessage `json:"job_data"`
		}

		if err := json.Unmarshal(m.Value, &event); err != nil {
			c.logger.Error("Failed to unmarshal message: ", err)
			continue
		}

		if event.Event == "job_queued" {
			go c.processJob(ctx, event.JobID, event.JobData)
		}
	}
}

func (c *Consumer) processJob(ctx context.Context, jobID string, jobData json.RawMessage) {
	var job scraper.Job
	if err := json.Unmarshal(jobData, &job); err != nil {
		c.logger.Error("Failed to unmarshal job: ", err)
		return
	}

	c.logger.Info("Processing job", "job_id", jobID)

	result, err := c.scraperPool.ExecuteJob(ctx, &job)
	if err != nil {
		c.logger.Error("Job failed", "job_id", jobID, "error", err)
		c.publishResult(ctx, jobID, result, err)
		return
	}

	c.logger.Info("Job completed", "job_id", jobID, "pages", result.PageCount)
	c.publishResult(ctx, jobID, result, nil)
}

func (c *Consumer) publishResult(ctx context.Context, jobID string, result *scraper.Result, err error) {
	// Publish to Redis for immediate API response
	data, _ := json.Marshal(result)
	c.redis.Publish(ctx, fmt.Sprintf("job:%s:result", jobID), data)
	
	// Store in Redis for persistence
	c.redis.Set(ctx, fmt.Sprintf("job:%s:data", jobID), data, 0)
}

// Stop stops the consumer
func (c *Consumer) Stop() error {
	if c.reader != nil {
		return c.reader.Close()
	}
	return nil
}