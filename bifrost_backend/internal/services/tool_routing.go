package services

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/smartcp/bifrost/internal/db"
	"github.com/smartcp/bifrost/internal/models"
)

// ToolRoutingService handles intelligent routing to tools
type ToolRoutingService struct {
	db           *db.PostgresDB
	toolRegistry *ToolRegistry
}

// NewToolRoutingService creates a new ToolRoutingService
func NewToolRoutingService(database *db.PostgresDB, toolRegistry *ToolRegistry) *ToolRoutingService {
	return &ToolRoutingService{
		db:           database,
		toolRegistry: toolRegistry,
	}
}

// RouteRequest routes a request to the most appropriate tool
func (trs *ToolRoutingService) RouteRequest(ctx context.Context, request string, context *string) (*models.RoutingDecision, error) {
	// For now, simple keyword matching
	// In production, this would use embeddings and semantic search

	// Get all tools
	tools, err := trs.toolRegistry.ListTools(ctx, nil, nil, 100, 0)
	if err != nil {
		return nil, fmt.Errorf("failed to list tools: %w", err)
	}

	if len(tools) == 0 {
		return nil, fmt.Errorf("no tools available for routing")
	}

	// Simple scoring based on keyword matching
	bestTool := tools[0]
	bestScore := 0.0
	reasoning := "No matching tool found, using default"

	requestLower := strings.ToLower(request)

	for _, tool := range tools {
		score := 0.0

		// Check name match
		if strings.Contains(requestLower, strings.ToLower(tool.Name)) {
			score += 0.5
		}

		// Check description match
		if strings.Contains(strings.ToLower(tool.Description), requestLower) {
			score += 0.3
		}

		// Check category match
		if strings.Contains(requestLower, strings.ToLower(tool.Category)) {
			score += 0.2
		}

		// Check tags match
		for _, tag := range tool.Tags {
			if strings.Contains(requestLower, strings.ToLower(tag)) {
				score += 0.1
			}
		}

		if score > bestScore {
			bestScore = score
			bestTool = tool
			reasoning = fmt.Sprintf("Matched based on keywords (score: %.2f)", score)
		}
	}

	// Normalize confidence to 0-1 range
	confidence := bestScore
	if confidence > 1.0 {
		confidence = 1.0
	}

	return &models.RoutingDecision{
		ToolID:     bestTool.ID,
		Tool:       bestTool,
		Confidence: confidence,
		Reasoning:  reasoning,
	}, nil
}

// ExtractParameters attempts to extract parameters from request
func (trs *ToolRoutingService) ExtractParameters(request string, tool *models.Tool) (string, error) {
	// Simple parameter extraction
	// In production, this would use LLM or structured extraction

	params := make(map[string]interface{})

	// Parse input schema to understand expected parameters
	var schema map[string]interface{}
	if err := json.Unmarshal([]byte(tool.InputSchema), &schema); err != nil {
		return "{}", fmt.Errorf("failed to parse input schema: %w", err)
	}

	// For now, just return empty parameters
	// Real implementation would extract from request based on schema
	paramsJSON, err := json.Marshal(params)
	if err != nil {
		return "{}", fmt.Errorf("failed to marshal parameters: %w", err)
	}

	return string(paramsJSON), nil
}
