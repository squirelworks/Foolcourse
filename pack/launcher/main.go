package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

func main() {
	exe, err := os.Executable()
	if err != nil {
		fail(err)
		os.Exit(1)
	}
	exe, err = filepath.EvalSymlinks(exe)
	if err != nil {
		fail(err)
		os.Exit(1)
	}
	home := filepath.Dir(exe)
	os.Setenv("FOOLCOURSE_HOME", home)
	os.Setenv("PYTHONPATH", filepath.Join(home, "app"))
	python := pythonPath(home)
	if _, err := os.Stat(python); err != nil {
		fail(err)
		os.Exit(1)
	}
	cmd := exec.Command(python, "-m", "foolcourse")
	cmd.Dir = home
	cmd.Env = os.Environ()
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fail(err)
		os.Exit(1)
	}
}

func pythonPath(home string) string {
	if runtime.GOOS == "windows" {
		windowed := filepath.Join(home, "python", "pythonw.exe")
		if _, err := os.Stat(windowed); err == nil {
			return windowed
		}
		return filepath.Join(home, "python", "python.exe")
	}
	return filepath.Join(home, "python", "bin", "python3")
}
