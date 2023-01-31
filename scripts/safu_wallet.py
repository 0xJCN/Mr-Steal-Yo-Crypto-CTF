from ape import accounts, project
from .utils.helper import w3, send_tx, MAX_UINT256

INITIAL_ETH_BALANCE = w3.to_wei(100, "ether")
ETH_WITHDRAWAL = w3.to_wei(50, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin2 = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ Admin 2: {admin2}\n⇒ Attacker: {attacker}\n---\n"
    )

    # deploy wallet library
    print("\n--- Deploying Wallet Library ---\n")
    project.SafuWalletLibrary.deploy(sender=admin)

    # deploy wallet
    print("\n--- Deploying Wallet ---\n")
    wallet = project.SafuWallet.deploy(
        [admin2.address],  # msg.sender is automatically considered an owner
        2,  # both admins required to execute transactions
        MAX_UINT256,  # max daily limit
        sender=admin,
    )

    # admin deposits 100 ETH to the wallet
    print("\n--- Admin is depositing 100 ETH into the Wallet ---\n")
    admin.transfer(wallet.address, INITIAL_ETH_BALANCE)
    assert wallet.balance == INITIAL_ETH_BALANCE

    # admin withdraws 50 ETH from the wallet
    print("\n--- Admin is withrawing 50 ETH from the Wallet ---\n")
    helper = project.Helper.deploy(sender=admin)
    calldata = helper.get_calldata(admin.address, ETH_WITHDRAWAL, "0x")
    tx = send_tx(admin, wallet.address, calldata)
    assert tx.logs

    assert wallet.balance == INITIAL_ETH_BALANCE - ETH_WITHDRAWAL

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After exploit: Attacker griefed Admin and they can not longer withdraw final 50 ETH ---\n"
    )

    # admin attempting to withdraw final 50 ETH - should revert
    bad_tx = send_tx(admin, wallet.address, calldata)
    assert not bad_tx.logs


if __name__ == "__main__":
    main()
