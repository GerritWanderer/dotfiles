local actions = require("fzf-lua").actions
return {
  "ibhagwan/fzf-lua",
  opts = {
    actions = {
      files = {
        ["enter"] = actions.file_edit,
      },
    },
  },
}
