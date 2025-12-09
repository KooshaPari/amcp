package cmd

import (
    "github.com/spf13/cobra"
    "smartcp/internal/services"
)

var buildCmd = &cobra.Command{
    Use:   "build",
    Short: "Build artifacts (wheels, go binaries)",
}

var buildWheelsCmd = &cobra.Command{
    Use:   "wheels",
    Short: "Build Python wheels into wheelhouse/",
    RunE: func(cmd *cobra.Command, args []string) error {
        return services.BuildWheels()
    },
}

var buildConstraintsCmd = &cobra.Command{
    Use:   "constraints",
    Short: "Generate constraints.txt",
    RunE: func(cmd *cobra.Command, args []string) error {
        return services.BuildConstraints()
    },
}

var buildGoCmd = &cobra.Command{
    Use:   "go",
    Short: "Build Go backend for host",
    RunE: func(cmd *cobra.Command, args []string) error {
        return services.BuildGo()
    },
}

func init() {
    buildCmd.AddCommand(buildWheelsCmd)
    buildCmd.AddCommand(buildConstraintsCmd)
    buildCmd.AddCommand(buildGoCmd)
}
