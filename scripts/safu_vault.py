from ape import accounts, project
from .utils.helper import w3, MAX_UINT256


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    user1 = accounts.test_accounts[1]
    user2 = accounts.test_accounts[2]
    admin = accounts.test_accounts[3]
    usdc_admin = accounts.test_accounts[4]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ USDC-Admin: {usdc_admin}\n⇒ Attacker: {attacker}\n⇒ User 1: {user1}"
    )
    print(f"⇒ User 2: {user2}\n---\n")

    # deploy USDC
    print("\n--- USDC Admin is deploying USDC contract ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=usdc_admin)

    # attacker and admin gets 10,000 USDC as starting funds
    amount = w3.to_wei(10000, "ether")
    usdc.mintPerUser(
        [attacker.address, admin.address], [amount, amount], sender=usdc_admin
    )

    # deploy safu strategy
    print("\n--- Deploying Safu Strategy ---\n")
    strategy = project.SafuStrategy.deploy(usdc.address, sender=admin)

    # deploy safu vault
    print("\n--- Deploying Safu Vault ---\n")
    vault = project.SafuVault.deploy(strategy.address, "LP Token", "LP", sender=admin)

    # set vault
    print("\n--- Setting Vault ---\n")
    strategy.setVault(vault.address, sender=admin)

    # other user deposits 10_000 USDC into the safu yield vault
    usdc.approve(vault.address, MAX_UINT256, sender=admin)
    vault.depositAll(sender=admin)

    # define initial balances for attacker and vault
    attacker_initial_bal = usdc.balanceOf(attacker.address) / 10**18
    vault_initial_bal = (
        usdc.balanceOf(vault.address) + usdc.balanceOf(strategy.address) / 10**18
    )

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Vault: {vault_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker drained >= 90% of funds from the Vault ---\n")

    # define ending balances for attacker and vault
    attacker_ending_bal = usdc.balanceOf(attacker.address) / 10**18
    vault_ending_bal = (
        usdc.balanceOf(vault.address) + usdc.balanceOf(strategy.address) / 10**18
    )

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n⇒ Vault: {vault_ending_bal}\n---\n"
    )

    total_vault_funds = usdc.balanceOf(vault.address) + usdc.balanceOf(strategy.address)
    assert total_vault_funds <= w3.to_wei(1000, "ether")
    assert usdc.balanceOf(attacker.address) >= w3.to_wei(19000, "ether")

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
