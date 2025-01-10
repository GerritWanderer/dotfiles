local actions = require("fzf-lua").actions
return {
  "ibhagwan/fzf-lua",
  opts = {
    files = {
      fzf_opts = {
        ["--history"] = vim.fn.stdpath("data") .. "/fzf-lua-files-history",
      },
    },
    grep = {
      fzf_opts = {
        ["--history"] = vim.fn.stdpath("data") .. "/fzf-lua-grep-history",
      },
    },
    actions = {
      files = {
        true,
        ["enter"] = actions.file_edit,
      },
    },
  },
}
