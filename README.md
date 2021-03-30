# Sentiment Flanders

Backend of the Twitter-base sentiment statistic, developed by [Radix](http://radix.ai).

* **VSA:** Reusens Michael <michael.reusens@vlaanderen.be>
* **Radix:**      Ruben Broekx <ruben@radix.ai>
* **Cloudar:**    Tom Mertens <tom.mertens@cloudar.be>

## Initial setup

### 1. Development environment setup

1. Install [VS Code](https://code.visualstudio.com/) as your editor. Your VS Code's _Workspace Settings_ are managed by this repo in `.vscode/settings.json`.
2. [Generate an SSH key](https://docs.gitlab.com/ee/ssh/README.html#generating-a-new-ssh-key-pair) for GitLab, [add the SSH key to GitLab](https://docs.gitlab.com/ee/ssh/README.html#adding-an-ssh-key-to-your-gitlab-account), and [add the SSH key to your authentication agent](https://docs.gitlab.com/ee/ssh/README.html#working-with-non-default-ssh-key-pair-paths).
3. Open a Terminal and clone this repo with `git clone git@gitlab.com:radix-ai/packages/sentiment-flanders.git`.
4. In VS Code open the repo folder and open an Integrated Terminal with <kbd>⌃</kbd> + <kbd>\`</kbd> and run `./tasks/init.sh` to:
   1. Install a set of recommended VS Code extensions ([Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python), [Cucumber](https://marketplace.visualstudio.com/items?itemName=alexkrechik.cucumberautocomplete), [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker), [Jira](https://marketplace.visualstudio.com/items?itemName=Atlassian.atlascode), [ShellCheck](https://marketplace.visualstudio.com/items?itemName=timonwong.shellcheck), [Terraform](https://marketplace.visualstudio.com/items?itemName=mauve.terraform)).
   2. Install [conda](https://docs.conda.io/projects/conda/en/latest/) for the current user, if not already installed.
   3. Create the conda environment `sentiment-flanders-env` in the repo's `.envs` directory (specified by merging `environment.*.yml`).
   4. Install the [pre-commit](https://pre-commit.com) hooks configured in `.pre-commit-config.yaml` and configure git.

### 2. Amazon Web Services setup

1. Ensure that you have a `~/.aws/credentials` file with your AWS organization account credentials:

```
[default]
aws_access_key_id={your access key id}
aws_secret_access_key={your secret access key}
```

2. Log on to the AWS organisation account at https://962194010810.signin.aws.amazon.com/console with your username and password. You must manage this login with LastPass!
3. Click on the _Switch Roles_ button for each of the below AWS workspace accounts:
   - [Infrastructure](https://signin.aws.amazon.com/switchrole?roleName=OrganizationAccountAccessRole&account=962194010810&displayName=sentiment-flanders-infrastructure&color=FBBF93)
   - [Feature](https://signin.aws.amazon.com/switchrole?roleName=OrganizationAccountAccessRole&account=962194010810&displayName=sentiment-flanders-feature&color=99BCE3)
   - [Development](https://signin.aws.amazon.com/switchrole?roleName=OrganizationAccountAccessRole&account=962194010810&displayName=sentiment-flanders-development&color=B7CA9D)
   - [Acceptance](https://signin.aws.amazon.com/switchrole?roleName=OrganizationAccountAccessRole&account=962194010810&displayName=sentiment-flanders-acceptance&color=FAD791)
   - [Production](https://signin.aws.amazon.com/switchrole?roleName=OrganizationAccountAccessRole&account=962194010810&displayName=sentiment-flanders-production&color=F2B0A9)
4. From now on, you can simply switch across AWS workspace accounts by clicking on your username in the top bar and selecting the desired workspace account under _Role History_.

## Contributing

### 1. Activating the Python environment

These steps are a prerequisite for any task you wish to run in this project:

1. Open any Python file in the project to load VS Code's Python extension, or skip this step if you have one open already.
2. Open a _new_ Integrated Terminal with <kbd>⌃</kbd> + <kbd>~</kbd> to activate the conda environment `sentiment-flanders-env` inside it.
3. Now you're ready to run any of tasks listed in `invoke --list`.

### 2. Unit testing

1. [Activate the Python environment](#1-activating-the-python-environment).
2. Run `invoke aws.role` to create a `.env` file so that the tests can be discovered and run with the right credentials. You might need to restart VS Code after this step.
3. If you don't see _⚡ Run tests_ in the blue bar, run <kbd>⌘</kbd> + <kbd>⇧</kbd> + <kbd>P</kbd> > _Python: Discover Tests_. Optionally debug the output in _View_ > _Output_ > _Python Test Log_ in case this step fails.
4. Go to any test function in `src/tests/pytest`.
5. Optional: put a breakpoint 🔴 next to the line number where you want to stop.
6. Click on _Run Test_ or _Debug Test_ above the test you want to debug.

### 3. Releasing a new version

1. [Activate the Python environment](#1-activating-the-python-environment).
2. Commit any (un)staged changes on your branch and make sure to test them with `invoke test`.
3. Run `invoke bump --part=[major|minor|patch|post]` to (a) update the version number, (b) commit the changes, and (c) tag the commit with a version identifier.
4. Your tags will be pushed to the remote next time you `git push` (because `push.followTags` is set to true in `.git/config`). Or push the tag manually with `git push origin v0.0.0`.
5. You can now `pip install git+ssh://git@gitlab.com/radix-ai/packages/sentiment-flanders.git@v0.0.0`.

### 4. Updating the Cookiecutter scaffolding

1. [Activate the Python environment](#1-activating-the-python-environment).
2. Run `brew install gpatch` to install GNU patch, which is currently required for cruft on macOS (see [cruft#8](https://github.com/timothycrosley/cruft/issues/8) on GitHub).
3. Run `cruft check` to check for updates.
4. Run `cruft update` to update to the latest scaffolding.

### 5. Serving FastAPI locally

1. [Activate the Python environment](#1-activating-the-python-environment).
2. Run `invoke serve` to launch [FastAPI](https://github.com/tiangolo/fastapi) at http://127.0.0.1:8000.
3. Alternatively, run <kbd>⌘</kbd> + <kbd>⇧</kbd> + <kbd>D</kbd> > _Uvicorn_ > _▶️ Start Debugging_.
