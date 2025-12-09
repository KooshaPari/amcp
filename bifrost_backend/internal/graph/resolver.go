package graph

import (
	"github.com/smartcp/bifrost/internal/db"
	"github.com/smartcp/bifrost/internal/services"
)

// Resolver is the root resolver
type Resolver struct {
	DB             *db.PostgresDB
	ToolRegistry   *services.ToolRegistry
	ToolRouting    *services.ToolRoutingService
	SemanticSearch *services.SemanticSearchService
	Execution      *services.ExecutionService
}
