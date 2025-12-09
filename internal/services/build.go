package services

import (
	"os/exec"
)

func BuildWheels() error {
	cmd := exec.Command("python", "-m", "build", "--wheel", "--outdir", "wheelhouse", ".")
	cmd.Stdout = logWriter("build-wheels")
	cmd.Stderr = logWriter("build-wheels")
	return cmd.Run()
}

func BuildConstraints() error {
	cmd := exec.Command("uv", "pip", "compile", "pyproject.toml", "--all-extras", "-o", "constraints.txt")
	cmd.Stdout = logWriter("build-constraints")
	cmd.Stderr = logWriter("build-constraints")
	return cmd.Run()
}

func BuildGo() error {
	cmd := exec.Command("bash", "-c", "cd bifrost_backend && go build -o ../bin/bifrost-backend ./cmd/server")
	cmd.Stdout = logWriter("build-go")
	cmd.Stderr = logWriter("build-go")
	return cmd.Run()
}
