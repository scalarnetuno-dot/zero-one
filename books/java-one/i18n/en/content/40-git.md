---
source_hash: 031640f7d604
title: "Git"
number: 40
part: p9
kicker: "The code says what the system does. The history says why — and it's the only part you can't rebuild."
goal: >-
  Version the project with commits that explain intent, work with branches
  and *pull requests*, and resolve a conflict without panic.
---

This is the chapter that should have been the first and is the
second-to-last, on purpose: Git only makes sense when there is something
with a story to tell. Aurora's project has forty chapters of decisions.

## The four everyday commands

```bash title="The whole cycle" numbered
git status                      # what changed
git add src/main/java/...       # choose what goes in
git commit -m "message"         # record
git push                        # publish
```

```bash title="Starting the project"
git init
echo "target/" > .gitignore
git add .
git commit -m "first commit: catalog skeleton"
git remote add origin git@github.com:aurora/catalog.git
git push -u origin main
```

:::pitfall
`target/`, `.idea/`, `*.class` and any file with a password **never** go
into the repository. A `.gitignore` forgotten on day one means, six months
later, a 400 MB repository full of compiled binaries. And an
`application.properties` with the database password under version control
means the password leaked — even if you delete it later, it stays in the
history forever.
:::

## A commit is a message to the future

:::compare left="What doesn't help" right="What explains"
tweaks

fixes

fix

wip

final update
---
fix N+1 in the
product listing

use @EntityGraph to
load the category
along: 4,032 queries
became 1
:::

The first group shows up in every repository in the world and is useless
on the day someone needs to understand why a line exists. The second
answers the only question the code doesn't answer on its own: **why**.

```text title="The format most teams adopt"
type: imperative summary, up to 50 characters

Optional body, explaining the reason and the context — not
what the diff already shows. Wrap at 72 columns.

Closes #42
```

| Type | When |
|---|---|
| `feat` | new feature |
| `fix` | defect fix |
| `refactor` | changes the shape, not the behavior |
| `test` | adds or fixes a test |
| `docs` | documentation |
| `chore` | build, dependency, configuration |

Table: The *Conventional Commits* convention. It lets you generate the
*changelog* automatically — and, more importantly, forces whoever writes
to classify their own change.

:::key
A good commit is **small and coherent**: one change, one reason. If the
message needs the word "and" twice, it's two commits. Splitting costs
thirty seconds; the benefit is being able to revert one without undoing
the other.
:::

## Branches

```bash title="The flow of a feature" numbered
git switch -c feat/search-by-name     # create and enter the branch

# ... work, commit ...

git push -u origin feat/search-by-name
# open the pull request in the GitHub interface

git switch main
git pull
git branch -d feat/search-by-name     # delete the local branch
```

:::diagram type="flowchart" caption="One branch per feature, review before it goes in."
nodes:
  - { id: m,  type: start,   text: "main" }
  - { id: b,  type: process, text: "feat/search-by-name" }
  - { id: c,  type: process, text: "commits" }
  - { id: pr, type: decision,text: "review approved?" }
  - { id: mg, type: process, text: "merge into main" }
  - { id: fx, type: process, text: "adjust and commit" }
edges:
  - { from: m,  to: b }
  - { from: b,  to: c }
  - { from: c,  to: pr }
  - { from: pr, to: mg, label: "yes" }
  - { from: pr, to: fx, label: "no" }
  - { from: fx, to: pr }
:::

A protected branch — a `main` that only accepts changes through an
approved *pull request*, with the tests from chapters 34 to 37 passing — is
the cheapest quality setup there is. It's two clicks in the GitHub
interface.

## Conflict: what it is and how to get out

```text title="The message that scares and shouldn't"
Auto-merging ProductService.java
CONFLICT (content): Merge conflict in ProductService.java
Automatic merge failed; fix conflicts and commit the result.
```

```java title="The file ends up like this" numbered
<<<<<<< HEAD
    return repository.findAll(pageable)
            .map(ProductResponse::of);
=======
    return repository.findAll(spec, pageable)
            .map(ProductResponse::of);
>>>>>>> feat/search-by-name
```

Between `<<<<<<<` and `=======` is your version; between `=======` and
`>>>>>>>`, the other branch's. You delete the markers and leave the correct
code — which may be one of the two, or a third thing that combines both.

```bash
git add ProductService.java
git commit          # the merge message comes ready-made
```

:::pitfall
A conflict isn't an error: it's Git saying two people changed the same
line and it has no way of guessing which one wins. Blindly accepting "my
version" to get rid of the screen is like deleting a colleague's work
without reading it — and it happens all the time. Read both sides. When in
doubt, call the person.
:::

## Undoing, without drama

```bash title="The four useful undos" numbered
git restore ProductService.java     # discard uncommitted change
git restore --staged file.java      # take it out of the "add"
git commit --amend                  # fix the last commit (local!)
git revert a1b2c3d                  # undo by creating another commit
```

:::pitfall
`git reset --hard` erases uncommitted work and there's no way back. And
`git push --force` rewrites the server's history: if someone had already
pulled that branch, their repository starts diverging from yours in a
confusing way. On a shared branch, undo with `revert`, which creates a new
commit and preserves the history.
:::

## History as a tool

```bash title="What you'll use when something breaks" numbered
git log --oneline -20
git log -p ProductService.java    # a file's history
git blame ProductService.java     # who wrote each line
git bisect start                  # find the commit that broke it
```

`git blame` has an unfair reputation as a tool for blaming. In practice,
it's the fastest path to **the commit message** that explains why that
strange line exists — and that's where the quality of the messages stops
being etiquette and becomes time saved.

:::story Works on my machine
The bug showed up on Thursday and only happened in staging.

Carlos ran it locally: it worked. Ran it again: it worked. He spent the
morning comparing configuration, Java version, PostgreSQL version.

At eleven thirty, Marina asked to see his `git status`.

```text
On branch feat/filters
Changes not staged for commit:
  modified:   src/main/resources/application.properties
  modified:   src/main/java/.../ProductSpecs.java
  modified:   src/main/java/.../SecurityConfig.java
```

Three files changed and not committed. It worked on Carlos's machine
because the fix existed only on Carlos's machine — in files he had touched
on Tuesday and forgotten.

"It's not that it works on your machine," said Marina. "It's that your
machine has software that doesn't exist anywhere else. Not even in the
repository."

In that afternoon's commit, Carlos wrote the longest message of his life.
Marina approved it without comments.
:::

:::summary
- `status`, `add`, `commit`, `push` cover the day; the rest is for when
  something goes wrong.
- `.gitignore` on day one; passwords never, in any commit.
- The message explains the **why**; the diff already shows the what.
- One branch per feature, `main` protected by *pull request* and tests.
- A conflict is a question, not an error. `revert` on a shared branch,
  never `push --force`.
:::

:::checkpoint
You version the project, write commits that explain intent, work on
branches with review and resolve a conflict by reading both sides.
:::

:::milestone
End of Part 9. The project has history, documentation that updates itself
and versioned requests. Everything that was missing for someone else to
take over the code — and that is exactly what Part 10 is going to ask of
you.
:::

:::exercise level=1
Initialize the repository, create the `.gitignore` and make the first
commit with a message that explains what the project is.

:::answer
A detail almost nobody does and that is worth a lot: write in the body of
the first commit **why** the project exists and what problem it solves.
It's the message the most people will read, and the only one nobody can
rebuild later.
:::

:::exercise level=2
Create a branch, change a line, go back to `main`, change the same line in
a different way and cause a conflict on purpose. Resolve it.

:::answer
Doing it on purpose, calmly, in a project that doesn't matter, is the
difference between freezing and solving it in two minutes on the day it
happens for real — which will be a Friday, in a hurry.
:::

:::exercise level=3
Use `git bisect` to find the commit that introduced a defect. Build the
scenario: ten commits, one of them breaking a test.

:::answer
`git bisect start`, `git bisect bad`, `git bisect good <old commit>`, and
Git does a binary search — ten commits become three or four checks. With a
test script, `git bisect run ./mvnw test` finds the culprit by itself. It
is Git's most underrated tool and the one that impresses most when you use
it in front of someone.
:::
