-- ┌─────────────────────┐
-- │ TypeScript LSP config│
-- └─────────────────────┘
--
-- Requires: tsgo (typescript-go, experimental)
-- Install:  https://github.com/microsoft/typescript-go
return {
  filetypes = {
    'javascript',
    'javascriptreact',
    'javascript.jsx',
    'typescript',
    'typescriptreact',
    'typescript.tsx',
  },
  settings = {
    typescript = {
      inlayHints = {
        parameterNames = {
          enabled = 'literals',
          suppressWhenArgumentMatchesName = true,
        },
        parameterTypes = { enabled = true },
        variableTypes = { enabled = true },
        propertyDeclarationTypes = { enabled = true },
        functionLikeReturnTypes = { enabled = true },
        enumMemberValues = { enabled = true },
      },
    },
  },
  on_attach = function(client, _)
    -- Slim down trigger characters for a less noisy completion experience
    client.server_capabilities.completionProvider.triggerCharacters =
      { '.', '"', "'", '`', '/', '@', '<' }
  end,
}
