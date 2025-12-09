package services

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/smartcp/bifrost/internal/db"
	"github.com/smartcp/bifrost/internal/models"
)

// ExecutionService handles tool execution
type ExecutionService struct {
	db          *db.PostgresDB
	toolRouting *ToolRoutingService
}

// NewExecutionService creates a new ExecutionService
func NewExecutionService(database *db.PostgresDB, toolRouting *ToolRoutingService) *ExecutionService {
	return &ExecutionService{
		db:          database,
		toolRouting: toolRouting,
	}
}

// ExecuteTool executes a tool with given parameters
func (es *ExecutionService) ExecuteTool(ctx context.Context, input *models.ExecuteToolInput) (*models.ExecutionResult, error) {
	startTime := time.Now()

	// Get tool
	tool, err := es.db.GetTool(ctx, input.ToolID)
	if err != nil {
		return nil, fmt.Errorf("failed to get tool: %w", err)
	}
	if tool == nil {
		return nil, fmt.Errorf("tool not found: %s", input.ToolID)
	}

	// Validate parameters against schema
	if err := es.validateParameters(input.Parameters, tool.InputSchema); err != nil {
		errMsg := fmt.Sprintf("invalid parameters: %v", err)
		return &models.ExecutionResult{
			Success:       false,
			ToolID:        input.ToolID,
			Error:         &errMsg,
			ExecutionTime: time.Since(startTime).Seconds(),
		}, nil
	}

	// Execute tool (mock implementation)
	result, err := es.executeMockTool(ctx, tool, input.Parameters, input.Context)
	if err != nil {
		errMsg := fmt.Sprintf("execution failed: %v", err)
		return &models.ExecutionResult{
			Success:       false,
			ToolID:        input.ToolID,
			Error:         &errMsg,
			ExecutionTime: time.Since(startTime).Seconds(),
		}, nil
	}

	output := result
	return &models.ExecutionResult{
		Success:       true,
		ToolID:        input.ToolID,
		Output:        &output,
		ExecutionTime: time.Since(startTime).Seconds(),
	}, nil
}

// validateParameters validates parameters against JSON schema
func (es *ExecutionService) validateParameters(parameters string, schema string) error {
	// Parse parameters
	var params map[string]interface{}
	if err := json.Unmarshal([]byte(parameters), &params); err != nil {
		return fmt.Errorf("invalid JSON: %w", err)
	}

	// Parse schema
	var schemaObj map[string]interface{}
	if err := json.Unmarshal([]byte(schema), &schemaObj); err != nil {
		return fmt.Errorf("invalid schema: %w", err)
	}

	// Basic validation - check required fields
	if properties, ok := schemaObj["properties"].(map[string]interface{}); ok {
		if required, ok := schemaObj["required"].([]interface{}); ok {
			for _, req := range required {
				field := req.(string)
				if _, exists := params[field]; !exists {
					return fmt.Errorf("missing required field: %s", field)
				}

				// Check type
				if propDef, ok := properties[field].(map[string]interface{}); ok {
					if propType, ok := propDef["type"].(string); ok {
						if !es.checkType(params[field], propType) {
							return fmt.Errorf("invalid type for field %s: expected %s", field, propType)
						}
					}
				}
			}
		}
	}

	return nil
}

// checkType checks if value matches expected JSON schema type
func (es *ExecutionService) checkType(value interface{}, expectedType string) bool {
	switch expectedType {
	case "string":
		_, ok := value.(string)
		return ok
	case "number":
		_, okFloat := value.(float64)
		_, okInt := value.(int)
		return okFloat || okInt
	case "boolean":
		_, ok := value.(bool)
		return ok
	case "object":
		_, ok := value.(map[string]interface{})
		return ok
	case "array":
		_, ok := value.([]interface{})
		return ok
	default:
		return true // Unknown types pass
	}
}

// executeMockTool executes a mock tool (placeholder for real execution)
func (es *ExecutionService) executeMockTool(ctx context.Context, tool *models.Tool, parameters string, context *string) (string, error) {
	// In production, this would call the actual tool endpoint
	// For now, return a mock response

	var params map[string]interface{}
	json.Unmarshal([]byte(parameters), &params)

	response := map[string]interface{}{
		"status":     "success",
		"tool":       tool.Name,
		"parameters": params,
		"result":     fmt.Sprintf("Successfully executed %s", tool.Name),
		"timestamp":  time.Now().Format(time.RFC3339),
	}

	if context != nil {
		response["context"] = *context
	}

	responseJSON, err := json.Marshal(response)
	if err != nil {
		return "", fmt.Errorf("failed to marshal response: %w", err)
	}

	return string(responseJSON), nil
}

// executeRemoteTool calls a remote tool endpoint
func (es *ExecutionService) executeRemoteTool(ctx context.Context, endpoint string, parameters string) (string, error) {
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, strings.NewReader(parameters))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to execute tool: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("tool returned status %d: %s", resp.StatusCode, string(body))
	}

	return string(body), nil
}
