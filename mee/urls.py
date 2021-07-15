import uritemplate

GITHUB = "https://api.github.com"
USERS = uritemplate.URITemplate(GITHUB + "/users{/name}")
GIST = uritemplate.URITemplate(GITHUB + "/users{/name}/gists{?page,since,per_page}")
