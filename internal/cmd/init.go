package cmd

import (
    "github.com/spf13/cobra"
    "smartcp/internal/config"
)

var initCmd = &cobra.Command{
    Use:   "init",
    Short: "Initialize user config (guided)",
    RunE: func(cmd *cobra.Command, args []string) error {
        return config.InitInteractive()
    },
}
