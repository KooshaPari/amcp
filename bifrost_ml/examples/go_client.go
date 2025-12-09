package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// Request/Response types matching Python API

type ClassifyRequest struct {
	Prompt  string         `json:"prompt"`
	Context map[string]any `json:"context"`
}

type ClassifyResponse struct {
	Complexity   string             `json:"complexity"`
	Confidence   float64            `json:"confidence"`
	ToolName     string             `json:"tool_name"`
	Alternatives []map[string]any   `json:"alternatives"`
}

type EmbedRequest struct {
	Texts []string `json:"texts"`
	Model string   `json:"model"`
}

type EmbedResponse struct {
	Embeddings [][]float64 `json:"embeddings"`
	ModelUsed  string      `json:"model_used"`
}

type RouteRequest struct {
	Prompt               string         `json:"prompt"`
	Context              map[string]any `json:"context"`
	OutputTokensEstimate int            `json:"output_tokens_estimate"`
}

type RouteResponse struct {
	Model              string  `json:"model"`
	Complexity         string  `json:"complexity"`
	EstimatedCostUSD   float64 `json:"estimated_cost_usd"`
	EstimatedLatencyMs int     `json:"estimated_latency_ms"`
	Rationale          string  `json:"rationale"`
	FallbackModel      *string `json:"fallback_model"`
}

type HealthResponse struct {
	Status        string `json:"status"`
	Version       string `json:"version"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// BifrostClient is a client for the Bifrost ML service
type BifrostClient struct {
	baseURL string
	client  *http.Client
}

// NewBifrostClient creates a new Bifrost ML client
func NewBifrostClient(baseURL string) *BifrostClient {
	return &BifrostClient{
		baseURL: baseURL,
		client:  &http.Client{},
	}
}

// HealthCheck checks if the service is healthy
func (c *BifrostClient) HealthCheck() (*HealthResponse, error) {
	resp, err := c.client.Get(c.baseURL + "/health")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

// Classify classifies a prompt
func (c *BifrostClient) Classify(prompt string, context map[string]any) (*ClassifyResponse, error) {
	req := ClassifyRequest{
		Prompt:  prompt,
		Context: context,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	resp, err := c.client.Post(
		c.baseURL+"/classify",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result ClassifyResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

// Embed generates embeddings for texts
func (c *BifrostClient) Embed(texts []string, model string) (*EmbedResponse, error) {
	req := EmbedRequest{
		Texts: texts,
		Model: model,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	resp, err := c.client.Post(
		c.baseURL+"/embed",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result EmbedResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

// Route routes a request to the optimal model
func (c *BifrostClient) Route(prompt string, context map[string]any, outputTokens int) (*RouteResponse, error) {
	req := RouteRequest{
		Prompt:               prompt,
		Context:              context,
		OutputTokensEstimate: outputTokens,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	resp, err := c.client.Post(
		c.baseURL+"/route",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result RouteResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

// ListModels lists available models
func (c *BifrostClient) ListModels() ([]string, error) {
	resp, err := c.client.Get(c.baseURL + "/models")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Models []string `json:"models"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result.Models, nil
}

func main() {
	// Example usage
	client := NewBifrostClient("http://localhost:8001")

	// Health check
	fmt.Println("Testing Bifrost ML Client\n")
	fmt.Println("1. Health Check")
	health, err := client.HealthCheck()
	if err != nil {
		panic(err)
	}
	fmt.Printf("   Status: %s, Version: %s, Uptime: %ds\n\n", health.Status, health.Version, health.UptimeSeconds)

	// List models
	fmt.Println("2. List Models")
	models, err := client.ListModels()
	if err != nil {
		panic(err)
	}
	fmt.Printf("   Available models: %v\n\n", models)

	// Classify
	fmt.Println("3. Classify Prompt")
	classify, err := client.Classify("What is the weather like?", map[string]any{})
	if err != nil {
		panic(err)
	}
	fmt.Printf("   Tool: %s, Complexity: %s, Confidence: %.2f\n\n",
		classify.ToolName, classify.Complexity, classify.Confidence)

	// Route
	fmt.Println("4. Route Request")
	route, err := client.Route(
		"Analyze this complex problem in detail",
		map[string]any{},
		1000,
	)
	if err != nil {
		panic(err)
	}
	fmt.Printf("   Model: %s, Complexity: %s, Cost: $%.4f, Latency: %dms\n",
		route.Model, route.Complexity, route.EstimatedCostUSD, route.EstimatedLatencyMs)
	fmt.Printf("   Rationale: %s\n\n", route.Rationale)

	// Embed
	fmt.Println("5. Generate Embeddings")
	embed, err := client.Embed([]string{"Hello world", "Machine learning"}, "mlx-embed")
	if err != nil {
		panic(err)
	}
	fmt.Printf("   Model: %s, Embeddings: %d vectors of dimension %d\n\n",
		embed.ModelUsed, len(embed.Embeddings), len(embed.Embeddings[0]))

	fmt.Println("All tests passed!")
}
