package cmd

import (
    "github.com/spf13/cobra"
    "smartcp/internal/services"
)

var logsCmd = &cobra.Command{
    Use:   "logs",
    Short: "Tail logs for SmartCP/Bifrost",
    RunE: func(cmd *cobra.Command, args []string) error {
        return services.TailLogs()
    },
}
