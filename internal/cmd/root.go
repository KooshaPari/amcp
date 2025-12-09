package cmd

import (
    "fmt"
    "os"

    "github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
    Use:   "smartcp",
    Short: "SmartCP CLI (user + dev)",
    Long:  "SmartCP CLI for configuring, inspecting, and running SmartCP and related services natively.",
}

func Execute() error {
    return rootCmd.Execute()
}

func init() {
    rootCmd.AddCommand(initCmd)
    rootCmd.AddCommand(statusCmd)
    rootCmd.AddCommand(configCmd)
    rootCmd.AddCommand(servicesCmd)
    rootCmd.AddCommand(logsCmd)
    rootCmd.AddCommand(buildCmd)
}

// common helpers
func exitErr(err error) {
    fmt.Fprintln(os.Stderr, err)
    os.Exit(1)
}
