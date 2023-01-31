from ape import accounts, project
from .utils.helper import w3


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

    # deploy core contracts
    print("\n--- Deploying Core Contracts ---\n")
    treasure_vault = project.TreasureVault.deploy(sender=admin)

    admin.transfer(treasure_vault.address, "2 ether")

    # admin generates signature for adminUser to withdraw funds from the TreasureVault
    helper = project.Helper.deploy(sender=admin)
    permit_hash = helper.get_permit_hash(
        treasure_vault.DOMAIN_SEPARATOR(),
        w3.to_wei(1, "ether"),
        0,
    )
    signature = w3.eth.account.signHash(permit_hash, admin.private_key)
    treasure_vault.sendFundsWithAuth(
        w3.to_wei(1, "ether"),
        0,
        signature.v,
        signature.r.to_bytes(32, byteorder="big"),
        signature.s.to_bytes(32, byteorder="big"),
        sender=admin_user,
    )

    # define initial balance for attacker and vault
    attacker_initial_bal = attacker.balance / 10**18
    vault_initial_bal = treasure_vault.balance / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Vault: {vault_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker drained all the ETH from the contract ---\n")

    # define ending balance for attacker and vault
    attacker_ending_bal = attacker.balance / 10**18
    vault_ending_bal = treasure_vault.balance / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n⇒ Vault: {vault_ending_bal}\n---\n"
    )

    # attacker drains ETH from contract
    assert attacker_ending_bal > attacker_initial_bal
    assert vault_ending_bal == 0

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
