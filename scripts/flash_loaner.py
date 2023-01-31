from ape import accounts, project
from .utils.helper import MAX_UINT256, w3, get_timestamp

INITIAL_LIQUIDITY = w3.to_wei(1_000_000, "ether")
ADMIN_USER_TOKENS = w3.to_wei(100_000, "ether")


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

    # deploy token contracts
    print("\n--- Deploying Token Contracts ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=admin)
    usdc.mintPerUser(
        [admin.address, admin_user.address],
        [INITIAL_LIQUIDITY, ADMIN_USER_TOKENS],
        sender=admin,
    )
    dai = project.Token.deploy("DAI", "DAI", sender=admin)
    dai.mintPerUser(
        [admin.address],
        [INITIAL_LIQUIDITY],
        sender=admin,
    )

    # deploy uniswap contracts
    print("\n--- Deploying Uniswap Contracts ---\n")
    weth = project.WETH9.deploy(sender=admin)
    factory = project.UniswapV2Factory.deploy(admin.address, sender=admin)
    router = project.UniswapV2Router02.deploy(
        factory.address, weth.address, sender=admin
    )

    # creating pair and adding initial liquidity
    print("\n--- Creating Pair and adding liquidity ---\n")
    usdc.approve(router.address, MAX_UINT256, sender=admin)
    dai.approve(router.address, MAX_UINT256, sender=admin)

    router.addLiquidity(  # creates pair
        usdc.address,
        dai.address,
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY,
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    pair = project.UniswapV2Pair.at(factory.getPair(usdc.address, dai.address))

    # initializing core contracts
    print("\n--- Setting up Core Contracts ---\n")
    flash_loaner = project.FlashLoaner.deploy(
        usdc.address, "fUSDC", "fUSDC", sender=admin
    )
    usdc.approve(flash_loaner.address, MAX_UINT256, sender=admin_user)
    flash_loaner.deposit(ADMIN_USER_TOKENS, admin_user.address, sender=admin_user)

    # define initial balance for attacker and flash loaner contract
    attacker_initial_bal = usdc.balanceOf(attacker.address) / 10**18
    flash_pool_initial_bal = usdc.balanceOf(flash_loaner.address) / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Pool: {flash_pool_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After exploit: Attacker drained over 99% of funds in the contract ---\n"
    )

    # define ending balance for attacker and flash loaner contract
    attacker_ending_bal = usdc.balanceOf(attacker.address) / 10**18
    flash_pool_ending_bal = usdc.balanceOf(flash_loaner.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n⇒ Pool: {flash_pool_ending_bal}\n---\n"
    )

    # attacker drains >= 99% of funds
    assert usdc.balanceOf(attacker.address) >= w3.to_wei(99_000, "ether")
    assert usdc.balanceOf(flash_loaner.address) <= w3.to_wei(1_000, "ether")

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
