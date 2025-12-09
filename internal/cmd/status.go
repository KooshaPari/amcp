package cmd

import (
    "fmt"

    "github.com/spf13/cobra"
    "smartcp/internal/services"
)

var statusCmd = &cobra.Command{
    Use:   "status",
    Short: "Show health of SmartCP/Bifrost services",
    RunE: func(cmd *cobra.Command, args []string) error {
        statuses, err := services.Health()
        if err != nil {
            return err
        }
        for _, s := range statuses {
            fmt.Printf("%-18s %s\n", s.Name, s.Status)
        }
        return nil
    },
}
