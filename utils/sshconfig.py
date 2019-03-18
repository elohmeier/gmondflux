import argparse
import logging
import os


from pathlib import Path

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def write_ssh_private_key(ssh_dir, env_name, filename):
    ssh_key = os.environ.get(env_name).replace("|", "\n")
    if not ssh_key:
        log.critical("no SSH key found in SSH_KEY environment variable, aborting")
        exit(1)
    ssh_id_path = ssh_dir / filename
    if ssh_id_path.exists():
        if ssh_id_path.read_text() == ssh_key:
            log.info("SSH key already present in %s", ssh_id_path)
        else:
            log.critical("%s already exists with different key, aborting", ssh_id_path)
            exit(1)
    else:
        ssh_id_path.write_text(ssh_key)
        ssh_id_path.chmod(0o400)
        log.info("SSH key written to %s", ssh_id_path)


def set_known_host(ssh_dir, public_key, filename):
    public_key_path = ssh_dir / filename
    if public_key_path.exists():
        raise NotImplementedError("cant handle existing known_hosts files")
    else:
        public_key_path.write_text(public_key)
        log.info("public key written to %s", public_key_path)


def ssh_config(private_key_env, private_key_filename, public_key, public_key_filename):
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    log.info("%s created/exists", ssh_dir)

    write_ssh_private_key(ssh_dir, private_key_env, private_key_filename)
    set_known_host(ssh_dir, public_key, public_key_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("configures ssh")
    parser.add_argument("--private-key-env", default="SSH_KEY")
    parser.add_argument("--private-key-filename", default="id_rsa")
    parser.add_argument(
        "--public-key",
        default="www.nerdworks.de,159.69.186.234 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPev8CW19Koi487ivLm3RtXfQuH6+IXLDm4H3TFmL0Xp",
    )
    parser.add_argument("--public-key-filename", default="known_hosts")
    args = parser.parse_args()

    ssh_config(
        args.private_key_env,
        args.private_key_filename,
        args.public_key,
        args.public_key_filename,
    )
