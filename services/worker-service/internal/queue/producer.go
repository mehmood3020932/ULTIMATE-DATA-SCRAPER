// internal/queue/producer.go
// Kafka producer for results

package queue

import (
	"context"
	"encoding/json"

	"github.com/segmentio/kafka-go"
)

type Producer struct {
	writer *kafka.Writer
}

func NewProducer(brokers []string, topic string) *Producer {
	return &Producer{
		writer: &kafka.Writer{
			Addr:     kafka.TCP(brokers...),
			Topic:    topic,
			Balancer: &kafka.LeastBytes{},
		},
	}
}

func (p *Producer) SendResult(ctx context.Context, jobID string, result interface{}) error {
	data, err := json.Marshal(result)
	if err != nil {
		return err
	}
	
	return p.writer.WriteMessages(ctx, kafka.Message{
		Key:   []byte(jobID),
		Value: data,
	})
}

func (p *Producer) Close() error {
	return p.writer.Close()
}