package services

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"

	"github.com/smartcp/bifrost/internal/db"
	"github.com/smartcp/bifrost/internal/models"
)

// SemanticSearchService handles vector-based semantic search
type SemanticSearchService struct {
	db                *db.PostgresDB
	embeddingEndpoint string
	embeddingAPIKey   string
}

// NewSemanticSearchService creates a new SemanticSearchService
func NewSemanticSearchService(database *db.PostgresDB) *SemanticSearchService {
	return &SemanticSearchService{
		db:                database,
		embeddingEndpoint: os.Getenv("EMBEDDING_ENDPOINT"),
		embeddingAPIKey:   os.Getenv("EMBEDDING_API_KEY"),
	}
}

// Search performs semantic search for tools
func (sss *SemanticSearchService) Search(ctx context.Context, query string, limit int, threshold float64) ([]*models.SearchResult, error) {
	// Get query embedding
	embedding, err := sss.getEmbedding(ctx, query)
	if err != nil {
		// Fall back to keyword search if embedding fails
		return sss.keywordSearch(ctx, query, limit)
	}

	// Perform vector search
	if threshold <= 0 {
		threshold = 0.7 // Default threshold
	}

	if limit <= 0 {
		limit = 10 // Default limit
	}

	return sss.db.SemanticSearch(ctx, embedding, limit, threshold)
}

// getEmbedding generates embedding for text
func (sss *SemanticSearchService) getEmbedding(ctx context.Context, text string) ([]float64, error) {
	// If no embedding endpoint configured, return error
	if sss.embeddingEndpoint == "" {
		return nil, fmt.Errorf("no embedding endpoint configured")
	}

	// Call embedding API
	reqBody := map[string]interface{}{
		"input": text,
		"model": "text-embedding-3-small",
	}

	reqJSON, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sss.embeddingEndpoint, strings.NewReader(string(reqJSON)))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if sss.embeddingAPIKey != "" {
		req.Header.Set("Authorization", "Bearer "+sss.embeddingAPIKey)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to call embedding API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("embedding API returned status %d: %s", resp.StatusCode, string(body))
	}

	var result struct {
		Data []struct {
			Embedding []float64 `json:"embedding"`
		} `json:"data"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if len(result.Data) == 0 {
		return nil, fmt.Errorf("no embedding returned")
	}

	return result.Data[0].Embedding, nil
}

// keywordSearch performs fallback keyword-based search
func (sss *SemanticSearchService) keywordSearch(ctx context.Context, query string, limit int) ([]*models.SearchResult, error) {
	// Simple keyword-based search as fallback
	queryLower := strings.ToLower(query)
	keywords := strings.Fields(queryLower)

	// Get all tools
	tools, err := sss.db.ListTools(ctx, nil, nil, 100, 0)
	if err != nil {
		return nil, fmt.Errorf("failed to list tools: %w", err)
	}

	// Score tools by keyword matches
	type scoredTool struct {
		tool  *models.Tool
		score float64
	}

	var scoredTools []scoredTool

	for _, tool := range tools {
		score := 0.0

		nameWords := strings.Fields(strings.ToLower(tool.Name))
		descWords := strings.Fields(strings.ToLower(tool.Description))

		for _, keyword := range keywords {
			// Check name
			for _, word := range nameWords {
				if strings.Contains(word, keyword) {
					score += 0.5
				}
			}

			// Check description
			for _, word := range descWords {
				if strings.Contains(word, keyword) {
					score += 0.3
				}
			}

			// Check tags
			for _, tag := range tool.Tags {
				if strings.Contains(strings.ToLower(tag), keyword) {
					score += 0.2
				}
			}
		}

		if score > 0 {
			scoredTools = append(scoredTools, scoredTool{tool: tool, score: score})
		}
	}

	// Sort by score
	for i := 0; i < len(scoredTools); i++ {
		for j := i + 1; j < len(scoredTools); j++ {
			if scoredTools[j].score > scoredTools[i].score {
				scoredTools[i], scoredTools[j] = scoredTools[j], scoredTools[i]
			}
		}
	}

	// Convert to search results
	var results []*models.SearchResult
	for i, st := range scoredTools {
		if i >= limit {
			break
		}
		results = append(results, &models.SearchResult{
			Tool:       st.tool,
			Similarity: st.score,
			Ranking:    i + 1,
		})
	}

	return results, nil
}
