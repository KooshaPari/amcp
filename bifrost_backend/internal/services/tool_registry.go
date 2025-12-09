package services

import (
	"context"
	"fmt"

	"github.com/smartcp/bifrost/internal/db"
	"github.com/smartcp/bifrost/internal/models"
)

// ToolRegistry manages tool registration and lookup
type ToolRegistry struct {
	db *db.PostgresDB
}

// NewToolRegistry creates a new ToolRegistry
func NewToolRegistry(database *db.PostgresDB) *ToolRegistry {
	return &ToolRegistry{db: database}
}

// RegisterTool registers a new tool
func (tr *ToolRegistry) RegisterTool(ctx context.Context, input *models.RegisterToolInput) (*models.Tool, error) {
	// Validate input
	if input.Name == "" {
		return nil, fmt.Errorf("tool name is required")
	}
	if input.Description == "" {
		return nil, fmt.Errorf("tool description is required")
	}
	if input.InputSchema == "" {
		return nil, fmt.Errorf("tool input schema is required")
	}

	// Create tool
	tool, err := tr.db.CreateTool(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to register tool: %w", err)
	}

	return tool, nil
}

// GetTool retrieves a tool by ID
func (tr *ToolRegistry) GetTool(ctx context.Context, id string) (*models.Tool, error) {
	return tr.db.GetTool(ctx, id)
}

// ListTools retrieves tools with filtering
func (tr *ToolRegistry) ListTools(ctx context.Context, category *string, tags []string, limit, offset int) ([]*models.Tool, error) {
	if limit <= 0 {
		limit = 100 // Default limit
	}
	if offset < 0 {
		offset = 0
	}

	return tr.db.ListTools(ctx, category, tags, limit, offset)
}

// UpdateTool updates an existing tool
func (tr *ToolRegistry) UpdateTool(ctx context.Context, id string, input *models.UpdateToolInput) (*models.Tool, error) {
	return tr.db.UpdateTool(ctx, id, input)
}

// DeleteTool deletes a tool
func (tr *ToolRegistry) DeleteTool(ctx context.Context, id string) error {
	return tr.db.DeleteTool(ctx, id)
}
