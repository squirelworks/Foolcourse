//go:build windows

package main

import (
	"os"
	"syscall"
	"unsafe"
)

func fail(err error) {
	msg := "Foolcourse could not start.\n\n" + err.Error()
	user32 := syscall.NewLazyDLL("user32.dll")
	box := user32.NewProc("MessageBoxW")
	title, _ := syscall.UTF16PtrFromString("Foolcourse")
	text, _ := syscall.UTF16PtrFromString(msg)
	box.Call(0, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(title)), 0x10)
	os.Stderr.WriteString(msg + "\n")
}
