from ape import accounts, project
from ape.utils import EMPTY_BYTES32
from .utils.helper import w3

USER_GOV_TOKENS = w3.to_wei(100_000, "ether")
ATTACKER_GOV_TOKENS = w3.to_wei(1, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin_user = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Attacker: {attacker}\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n---\n"
    )

    # deploying token contracts
    print("\n--- Deploying Token Contracts ---\n")
    gov = project.Token.deploy("GOV", "GOV", sender=admin)
    gov.mintPerUser(
        [admin_user.address, attacker.address],
        [USER_GOV_TOKENS, ATTACKER_GOV_TOKENS],
        sender=admin,
    )

    # deploying core contracts
    print("\n--- Deploying Core Contracts ---\n")
    address_registry = project.AddressRegistry.deploy(sender=admin)

    revest = project.Revest.deploy(address_registry.address, sender=admin)

    lock_manager = project.LockManager.deploy(address_registry.address, sender=admin)

    token_vault = project.TokenVault.deploy(address_registry.address, sender=admin)

    fnft_handler = project.FNFTHandler.deploy(address_registry.address, sender=admin)

    address_registry.setLockManager(lock_manager.address, sender=admin)
    address_registry.setTokenVault(token_vault.address, sender=admin)
    address_registry.setRevestFNFT(fnft_handler.address, sender=admin)
    address_registry.setRevest(revest.address, sender=admin)

    # --adminUser deposits GOV token into Revest vault
    print("\n--- Admin User is depositing GOV tokens into Vault ---\n")
    gov.approve(revest.address, USER_GOV_TOKENS, sender=admin_user)
    revest.mintAddressLock(
        admin_user.address,
        EMPTY_BYTES32,
        [admin_user.address],
        [100],
        (gov.address, w3.to_wei(1_000, "ether"), 0),
        sender=admin_user,
    )

    # define initial balance for attacker and revest contract
    attacker_initial_bal = gov.balanceOf(attacker.address) / 10**18
    vault_initial_bal = gov.balanceOf(token_vault.address) / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Revest Contract: {vault_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After exploit: Attacker acquired all GOV tokens from Revest Contract ---\n"
    )

    # define ending balance for attacker and revest contract
    attacker_ending_bal = gov.balanceOf(attacker.address) / 10**18
    vault_ending_bal = gov.balanceOf(token_vault.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n⇒ Revest Contract: {vault_ending_bal}\n---\n"
    )

    # attacker acquires all GOV tokens that were deposited into the Revest contract
    assert gov.balanceOf(token_vault.address) == 0
    assert gov.balanceOf(attacker.address) == USER_GOV_TOKENS + ATTACKER_GOV_TOKENS

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
