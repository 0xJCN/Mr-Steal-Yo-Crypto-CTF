from ape import accounts, project
from .utils.helper import get_timestamp, w3

STRIKE_PRICE = w3.to_wei(2_000, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin_user = accounts.test_accounts[2]
    admin_user_2 = accounts.test_accounts[3]
    admin_user_3 = accounts.test_accounts[4]
    admin_user_4 = accounts.test_accounts[5]
    admin_user_5 = accounts.test_accounts[6]

    admin_user_accounts = [
        admin_user,
        admin_user_2,
        admin_user_3,
        admin_user_4,
        admin_user_5,
    ]

    print(
        f"\n--- \nOur players:\n⇒ Attacker: {attacker}\n⇒ Admin: {admin}\n⇒ Admin User 1: {admin_user}\n⇒ Admin User 2: {admin_user_2}"
    )
    print(
        f"⇒ Admin User 3: {admin_user_3}\n⇒ Admin User 4: {admin_user_4}\n⇒ Admin User 5: {admin_user_5}\n---\n"
    )

    # deploy token
    print("\n--- Deploying and minting USDC ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=admin)
    usdc.mintPerUser(
        admin_user_accounts,
        [STRIKE_PRICE] * len(admin_user_accounts),  # strike price
        sender=admin,
    )
    usdc.mintPerUser(
        [attacker.address], [w3.to_wei(500, "ether")], sender=admin
    )  # attacker starts with 500 usdc

    # deploy core contracts
    print("\n--- Deploying Core Contracts ---\n")
    options_market = project.OptionsMarket.deploy(usdc.address, sender=admin)

    options_contract = project.OptionsContract.deploy(
        usdc.address,
        2_000,  # strike price of 2000 USDC per ETH
        get_timestamp() * (60 * 60),  # 1 hr expiry
        options_market.address,
        sender=admin,
    )
    options_market.setPrice(100, sender=admin)  # 100 USDC premium per oToken

    options_market.setOptionsContract(options_contract.address, sender=admin)

    # -- adminUser(s) purchase 1 option each
    print("\n--- Admin Users are purchasing 1 option each ---\n")
    for user in admin_user_accounts:
        usdc.approve(options_contract.address, STRIKE_PRICE, sender=user)
        options_contract.createAndSellERC20CollateralOption(STRIKE_PRICE, sender=user)

    # define initial balance for attacker and options contract
    attacker_initial_eth_bal = attacker.balance
    attacker_initial_bal = usdc.balanceOf(attacker.address) / 10**18
    contract_initial_bal = usdc.balanceOf(options_contract.address) / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Options Contract: {contract_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker acquired all USDC from Options Contract ---\n")

    # define ending balance for attacker and options contract
    attacker_ending_bal = usdc.balanceOf(attacker.address) / 10**18
    contract_ending_bal = usdc.balanceOf(options_contract.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n⇒ Options Contract: {contract_ending_bal}\n---\n"
    )

    # attacker acquires all USDC from options contract - doesn't use more than 1 ETH + gas
    assert usdc.balanceOf(options_contract.address) == 0
    assert usdc.balanceOf(attacker.address) >= w3.to_wei(10_000, "ether")
    assert attacker.balance >= attacker_initial_eth_bal - (w3.to_wei(11, "ether") / 10)

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
