//SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@openzeppelin/access/Ownable.sol";
import "@openzeppelin/token/ERC20/IERC20.sol";
import "@openzeppelin/token/ERC20/utils/SafeERC20.sol";


interface ISafuFactory {
    function getPair(address, address) external returns (address);
}

interface ISafuPair {
    function getReserves() external view returns (
        uint112 _reserve0, 
        uint112 _reserve1, 
        uint32 _blockTimestampLast
    );
    function token0() external view returns (address);
    function balanceOf(address) external view returns (uint256);
    function burn(address) external returns (uint256 amount0, uint256 amount1);
    function swap(
        uint amount0Out, 
        uint amount1Out, 
        address to, 
        bytes calldata data
    ) external;
}

// SafuMakerV2 is SafuSwap's left hand and kinda a wizard. He can cook up SAFU from pretty much anything!
// This contract handles "serving up" rewards for xSAFU holders by trading tokens collected from fees.
// SafuSwap's rewards are generated by swaping rewards to SAFU and sending to bar address for distribution
contract SafuMakerV2 is Ownable {

    using SafeERC20 for IERC20;

    ISafuFactory public immutable factory;
    address public immutable bar; // staking contract for disseminating tokens to users
    address private immutable safu; // SAFU is the farm token
    address private immutable usdc; // USDC is the base token for most trading pairs (rather than ETH/etc.)

    mapping(address => address) internal _bridges;

    event LogBridgeSet(address indexed token, address indexed bridge);

    modifier onlyEOA() {
        require(msg.sender == tx.origin, "SafuMakerV2: must use EOA");
        _;
    }

    constructor(
        address _factory,
        address _bar,
        address _safu,
        address _usdc
    ) public {
        factory = ISafuFactory(_factory);
        bar = _bar;
        safu = _safu;
        usdc = _usdc;
    }

    /// @dev converts single pair into SAFU token for xSAFU holders
    function convert(address token0, address token1) external onlyEOA {
        _convert(token0, token1);
    }

    /// @dev user can specify which pair to convert tokens to SAFU for xSAFU holders
    function convertMultiple(address[] calldata token0, address[] calldata token1) external onlyEOA {
        require(token0.length == token1.length, "SafuMakerV2: token lengths don't match");

        for (uint256 i=0; i<token0.length; i++) {
            _convert(token0[i], token1[i]);
        }
    }

    /// @dev returns the bridging token to perform swaps between other tokens
    function bridgeFor(address token) public view returns (address bridge) {
        bridge = _bridges[token];
        if (bridge == address(0)) {
            bridge = usdc;
        }
    }

    /// @dev converts a single trading pair's rewards into SAFU token
    function _convert(address token0, address token1) internal {
        ISafuPair pair = ISafuPair(factory.getPair(token0, token1));

        require(address(pair) != address(0), "SafuMakerV2: Invalid pair");
        
        IERC20(address(pair)).safeTransfer(address(pair), pair.balanceOf(address(this)));

        // We don't take amount0 and amount1 from here, as it won't take into account reflect tokens.
        pair.burn(address(this));

        // We get the amount0 and amount1 by their respective balance of SafuMakerV2.
        uint256 amount0 = IERC20(token0).balanceOf(address(this));
        uint256 amount1 = IERC20(token1).balanceOf(address(this));

        _convertStep(token0, token1, amount0, amount1);
    }

    /// @dev converts all tokens to SAFU token
    function _convertStep(
        address token0,
        address token1,
        uint256 amount0,
        uint256 amount1
    ) internal returns (uint256 safuOut) {
        if (token0 == token1) {
            uint256 amount = amount0 + (amount1);
            if (token0 == safu) {
                IERC20(safu).safeTransfer(bar, amount);
                safuOut = amount;
            } else if (token0 == usdc) {
                safuOut = _toSafu(usdc, amount);
            } else {
                address bridge = bridgeFor(token0);
                amount = _swap(token0, bridge, amount, address(this));
                safuOut = _convertStep(bridge, bridge, amount, 0); // recursive
            }

        } else if (token0 == safu) {
            IERC20(safu).safeTransfer(bar, amount0);
            safuOut = _toSafu(token1, amount1) + (amount0);
        } else if (token1 == safu) {
            IERC20(safu).safeTransfer(bar, amount1);
            safuOut = _toSafu(token0, amount0) + (amount1);

        } else if (token0 == usdc) {
            safuOut = _toSafu(usdc, _swap(token1, usdc, amount1, address(this)) + (amount0));
        } else if (token1 == usdc) {
            safuOut = _toSafu(usdc, _swap(token0, usdc, amount0, address(this)) + (amount1));

        } else {
            address bridge0 = bridgeFor(token0);
            address bridge1 = bridgeFor(token1);
            if (bridge0 == token1) {
                safuOut = _convertStep(bridge0, token1, _swap(token0, bridge0, amount0, address(this)), amount1);
            } else if (bridge1 == token0) {
                safuOut = _convertStep(token0, bridge1, amount0, _swap(token1, bridge1, amount1, address(this)));
            } else {
                safuOut = _convertStep(
                    bridge0,
                    bridge1,
                    _swap(token0, bridge0, amount0, address(this)),
                    _swap(token1, bridge1, amount1, address(this))
                );
            }
        }
    }

    /// @dev functionality to swap between arbitrary tokens
    function _swap(
        address fromToken,
        address toToken,
        uint256 amountIn,
        address to
    ) internal returns (uint256 realAmountOut) {
        ISafuPair pair = ISafuPair(factory.getPair(fromToken, toToken));
        require(address(pair) != address(0), "SafuMakerV2: Cannot convert");

        (uint256 reserve0, uint256 reserve1, ) = pair.getReserves();

        IERC20(fromToken).safeTransfer(address(pair), amountIn);

        // Added in case fromToken is a reflect token.
        if (fromToken == pair.token0()) {
            amountIn = IERC20(fromToken).balanceOf(address(pair)) - reserve0;
        } else {
            amountIn = IERC20(fromToken).balanceOf(address(pair)) - reserve1;
        }

        uint256 balanceBefore = IERC20(toToken).balanceOf(to);

        uint256 amountInWithFee = amountIn * (997);
        if (fromToken == pair.token0()) {
            uint256 amountOut = (amountInWithFee * (reserve1)) / ((reserve0 * (1000)) + (amountInWithFee));
            pair.swap(0, amountOut, to, new bytes(0));
        } else {
            uint256 amountOut = (amountInWithFee * (reserve0)) / ((reserve1 * (1000)) + (amountInWithFee));
            pair.swap(amountOut, 0, to, new bytes(0));
        }

        realAmountOut = IERC20(toToken).balanceOf(to) - balanceBefore;
    }

    /// @dev swap from any token to SAFU token
    function _toSafu(address token, uint256 amountIn) internal returns (uint256 amountOut) {
        amountOut = _swap(token, safu, amountIn, bar);
    }

    /// @dev set the intermediary bridge for a token and other tokens
    function setBridge(address token, address bridge) external onlyOwner {
        require(token != safu && token != usdc && token != bridge, "SafuMakerV2: Invalid bridge");

        _bridges[token] = bridge;
        emit LogBridgeSet(token, bridge);
    }

}

