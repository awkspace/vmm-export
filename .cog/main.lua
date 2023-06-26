task {
  name = "build",
  description = "Build Docker image.",
  run = function()
    sh.docker.build{t="awkspace/vmm-export", "."}
  end
}

task {
  name = "push",
  description = "Push latest tagged Docker image.",
  run = function()
    sh.docker.push("awkspace/vmm-export")
  end
}

task {
  name = "fmt",
  description = "Run code formatters.",
  run = function()
    sh.isort(".")
    sh.black{["line-length"]=80, "."}
  end
}
