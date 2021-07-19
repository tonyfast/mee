# `mee` content management

![](https://raw.githubusercontent.com/deathbeds/drawins/master/mee%20you%20small.jpg)

writing is good for your health, and `mee` is here to help you publish your writing.
`mee` gives meaning to Github's `gist` service, by turning them into a blog/documentation content.

## how it works

each night, `mee` publishes a new version of your work if you created or updated your gist.

### publishing

1. ask github for new gist information
2. add gist to your `username/` folder as `git submodule`
3. generate documentation configuration files
4. build documentation and deploy to the `gh-pages` break

### adding content

1. create a gist
2. work on it throughout the week
3. get some rest at night and check out your published content in the morning
    * alternatively, force a build by rerunning the latest github workflow.

### deployment

we suggest deploying `mee` on your [github profile readme](https://docs.github.com/en/github/setting-up-and-managing-your-github-profile/customizing-your-profile/managing-your-profile-readme). you'll add a single github action workflow file that does rest of the work.

### examples

* https://tonyfast.github.io/tonyfast

## roadmap

* [x] `jupyter_book and sphinx`
* [ ] `nikola`
* [ ] `mkdocs`
* [ ] designed defaults