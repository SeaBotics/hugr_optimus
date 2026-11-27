# External physical library dependencies

## Dependencies description

* **Joystick_drivers**: Let's the user run nodes such that a controller will automatically get registered and recieve streamed data through serial.

## How to add an external repository to github

Within the folder `~/hugr_optimus/Dependencies/`, use:

```bash
git submodule add https://github.com/<user>/<repo>
```

(after `add`, use the HTTPS link to the repository)

If github does not download the submodule directly, use:

```bash
git submodule update --init --recursive
```


