package db

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/lib/pq"
	_ "github.com/lib/pq"
	"github.com/smartcp/bifrost/internal/models"
)

// PostgresDB wraps database connection
type PostgresDB struct {
	conn *sql.DB
}

// NewPostgresDB creates a new Postgres database connection
func NewPostgresDB(connString string) (*PostgresDB, error) {
	conn, err := sql.Open("postgres", connString)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := conn.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &PostgresDB{conn: conn}, nil
}

// Close closes the database connection
func (db *PostgresDB) Close() error {
	return db.conn.Close()
}

// GetTool retrieves a tool by ID
func (db *PostgresDB) GetTool(ctx context.Context, id string) (*models.Tool, error) {
	query := `
		SELECT id, name, description, input_schema, category, tags, embedding, metadata, created_at, updated_at
		FROM tools
		WHERE id = $1 AND deleted_at IS NULL
	`

	var tool models.Tool
	var tags pq.StringArray
	var embedding pq.Float64Array

	err := db.conn.QueryRowContext(ctx, query, id).Scan(
		&tool.ID, &tool.Name, &tool.Description, &tool.InputSchema,
		&tool.Category, &tags, &embedding, &tool.Metadata,
		&tool.CreatedAt, &tool.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get tool: %w", err)
	}

	tool.Tags = tags
	tool.Embedding = embedding

	return &tool, nil
}

// ListTools retrieves tools with optional filtering
func (db *PostgresDB) ListTools(ctx context.Context, category *string, tags []string, limit, offset int) ([]*models.Tool, error) {
	query := `
		SELECT id, name, description, input_schema, category, tags, metadata, created_at, updated_at
		FROM tools
		WHERE deleted_at IS NULL
	`

	args := []interface{}{}
	argNum := 1

	if category != nil {
		query += fmt.Sprintf(" AND category = $%d", argNum)
		args = append(args, *category)
		argNum++
	}

	if len(tags) > 0 {
		query += fmt.Sprintf(" AND tags && $%d", argNum)
		args = append(args, pq.Array(tags))
		argNum++
	}

	query += " ORDER BY created_at DESC"

	if limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argNum)
		args = append(args, limit)
		argNum++
	}

	if offset > 0 {
		query += fmt.Sprintf(" OFFSET $%d", argNum)
		args = append(args, offset)
	}

	rows, err := db.conn.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list tools: %w", err)
	}
	defer rows.Close()

	var tools []*models.Tool
	for rows.Next() {
		var tool models.Tool
		var tags pq.StringArray

		err := rows.Scan(
			&tool.ID, &tool.Name, &tool.Description, &tool.InputSchema,
			&tool.Category, &tags, &tool.Metadata,
			&tool.CreatedAt, &tool.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan tool: %w", err)
		}

		tool.Tags = tags
		tools = append(tools, &tool)
	}

	return tools, nil
}

// CreateTool creates a new tool
func (db *PostgresDB) CreateTool(ctx context.Context, input *models.RegisterToolInput) (*models.Tool, error) {
	metadata := "{}"
	if input.Metadata != nil {
		metadata = *input.Metadata
	}

	query := `
		INSERT INTO tools (name, description, input_schema, category, tags, metadata)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, name, description, input_schema, category, tags, metadata, created_at, updated_at
	`

	var tool models.Tool
	var tags pq.StringArray

	err := db.conn.QueryRowContext(ctx, query,
		input.Name, input.Description, input.InputSchema, input.Category,
		pq.Array(input.Tags), metadata,
	).Scan(
		&tool.ID, &tool.Name, &tool.Description, &tool.InputSchema,
		&tool.Category, &tags, &tool.Metadata,
		&tool.CreatedAt, &tool.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create tool: %w", err)
	}

	tool.Tags = tags

	return &tool, nil
}

// UpdateTool updates an existing tool
func (db *PostgresDB) UpdateTool(ctx context.Context, id string, input *models.UpdateToolInput) (*models.Tool, error) {
	// Build dynamic update query
	updates := []string{}
	args := []interface{}{}
	argNum := 1

	if input.Name != nil {
		updates = append(updates, fmt.Sprintf("name = $%d", argNum))
		args = append(args, *input.Name)
		argNum++
	}

	if input.Description != nil {
		updates = append(updates, fmt.Sprintf("description = $%d", argNum))
		args = append(args, *input.Description)
		argNum++
	}

	if input.InputSchema != nil {
		updates = append(updates, fmt.Sprintf("input_schema = $%d", argNum))
		args = append(args, *input.InputSchema)
		argNum++
	}

	if input.Category != nil {
		updates = append(updates, fmt.Sprintf("category = $%d", argNum))
		args = append(args, *input.Category)
		argNum++
	}

	if input.Tags != nil {
		updates = append(updates, fmt.Sprintf("tags = $%d", argNum))
		args = append(args, pq.Array(*input.Tags))
		argNum++
	}

	if input.Metadata != nil {
		updates = append(updates, fmt.Sprintf("metadata = $%d", argNum))
		args = append(args, *input.Metadata)
		argNum++
	}

	if len(updates) == 0 {
		return db.GetTool(ctx, id)
	}

	updates = append(updates, "updated_at = NOW()")
	args = append(args, id)

	query := fmt.Sprintf(`
		UPDATE tools
		SET %s
		WHERE id = $%d AND deleted_at IS NULL
		RETURNING id, name, description, input_schema, category, tags, metadata, created_at, updated_at
	`, join(updates, ", "), argNum)

	var tool models.Tool
	var tags pq.StringArray

	err := db.conn.QueryRowContext(ctx, query, args...).Scan(
		&tool.ID, &tool.Name, &tool.Description, &tool.InputSchema,
		&tool.Category, &tags, &tool.Metadata,
		&tool.CreatedAt, &tool.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to update tool: %w", err)
	}

	tool.Tags = tags

	return &tool, nil
}

// DeleteTool soft deletes a tool
func (db *PostgresDB) DeleteTool(ctx context.Context, id string) error {
	query := `
		UPDATE tools
		SET deleted_at = NOW()
		WHERE id = $1 AND deleted_at IS NULL
	`

	result, err := db.conn.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete tool: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("tool not found")
	}

	return nil
}

// SemanticSearch performs vector similarity search
func (db *PostgresDB) SemanticSearch(ctx context.Context, queryEmbedding []float64, limit int, threshold float64) ([]*models.SearchResult, error) {
	query := `
		SELECT 
			id, name, description, input_schema, category, tags, metadata, created_at, updated_at,
			1 - (embedding <=> $1::vector) as similarity
		FROM tools
		WHERE deleted_at IS NULL
			AND 1 - (embedding <=> $1::vector) > $2
		ORDER BY embedding <=> $1::vector
		LIMIT $3
	`

	// Convert embedding to string format for pgvector
	embeddingJSON, err := json.Marshal(queryEmbedding)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal embedding: %w", err)
	}

	rows, err := db.conn.QueryContext(ctx, query, string(embeddingJSON), threshold, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to search: %w", err)
	}
	defer rows.Close()

	var results []*models.SearchResult
	ranking := 1

	for rows.Next() {
		var tool models.Tool
		var tags pq.StringArray
		var similarity float64

		err := rows.Scan(
			&tool.ID, &tool.Name, &tool.Description, &tool.InputSchema,
			&tool.Category, &tags, &tool.Metadata,
			&tool.CreatedAt, &tool.UpdatedAt,
			&similarity,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan result: %w", err)
		}

		tool.Tags = tags

		results = append(results, &models.SearchResult{
			Tool:       &tool,
			Similarity: similarity,
			Ranking:    ranking,
		})
		ranking++
	}

	return results, nil
}

// Helper function to join strings
func join(strs []string, sep string) string {
	if len(strs) == 0 {
		return ""
	}
	result := strs[0]
	for i := 1; i < len(strs); i++ {
		result += sep + strs[i]
	}
	return result
}
