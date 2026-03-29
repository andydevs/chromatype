using System.Runtime.CompilerServices;
using UnityEngine;
using UnityEngine.InputSystem;

public class FPSMoveControl : MonoBehaviour
{
    private CharacterController player;
    private const float GRAVITY = 9.81f;

    public InputActionReference moveAction;

    public InputActionReference jumpAction;

    [Range(0.1f, 15.0f)]
    public float moveSpeed = 10.0f;

    [Range(0.1f, 10.0f)]
    public float jumpHeight = 5.0f;

    private float verticalVelocity;

    private const float MAX_GROUND_VELOCITY = -2.0f;

    void Start()
    {
        player = GetComponent<CharacterController>();
        jumpAction.action.performed += OnJumpPerformed;
        verticalVelocity = 0.0f;
    }

    void Update()
    {
        // Horizontal motion
        var stick = moveAction.action.ReadValue<Vector2>();
        var velocityXZ = moveSpeed * (transform.forward * stick.y + transform.right * stick.x);

        // Gravity and vertical motion
        if (!player.isGrounded)
            verticalVelocity -= GRAVITY * Time.deltaTime;
        else
            verticalVelocity = Mathf.Max(verticalVelocity, MAX_GROUND_VELOCITY);
        var velocityY = Vector3.up * verticalVelocity;

        // Move player
        player.Move((velocityXZ + velocityY) * Time.deltaTime);
    }

    void OnJumpPerformed(InputAction.CallbackContext _ctx)
    {
        if (player.isGrounded)
        {
            verticalVelocity = Mathf.Sqrt(jumpHeight * 2 * GRAVITY);
        }
    }

}
