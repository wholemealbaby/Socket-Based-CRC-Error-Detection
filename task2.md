COSC1111/3113 – Assignment 3 – Group 33 

Nikolas Papakalodoukas, s4094240@student.rmit.edu.au 

Thomas Gosling, s3850201@student.rmit.edu.au 

Jayden Bolth, s4104354@student.rmit.edu.au 

Alexandre Lee, s4090276@student.rmit.edu.au 

1   Introduction 

Cyclic Redundancy Check (CRC) is used to detect accidental changes in binary data. Lab 6 placed this concept inside a Python socket program so that CRC was not only a mathematical calculation, but part of a sender-receiver communication process. The original lab structure used a client program to produce and send a CRC codeword and a server program to validate the received codeword. 

This essay addresses three questions. First, it explains the situation in which a CRC implementation is provided with socket programming. Second, it describes how ChatGPT can be used to rewrite the required Python code. Third, it explains how the rewritten code should be tested, including the normal success case and a deliberately corrupted message case.  

2   Main content  

2.1   Situation in Which CRC is Provided with Socket Programming 

CRC is provided with socket programming when the purpose is to check message integrity across a communication boundary. In a standalone CRC program, the data and the checking result remain inside one process. In a socket program, the data is prepared by one process, transmitted through a network interface, received by another process, and then checked. This makes the CRC calculation part of a communication protocol rather than a separate arithmetic exercise.  

The Lab 6 situation is a sender-receiver model. The client represents the sending host. It accepts a binary string, calculates CRC bits, appends those bits to form a codeword, and sends the codeword through a TCP socket. The server represents the receiving host. It accepts the socket connection, reads the codeword, performs the CRC division on the received string, and decides whether the message should be accepted or rejected. In this setting, CRC is used after reception to verify whether the transmitted codeword is still consistent with the agreed divisor.  

This situation also shows an important protocol design idea. Even though TCP already includes reliability mechanisms, the lab-level CRC check demonstrates how an application or protocol layer can perform its own integrity decision. The sender and receiver must agree on the same divisor, and the receiver must test the full codeword, not only the original data. Therefore, the appropriate situation for this CRC implementation is a client-server exchange where the receiver needs independent evidence that a binary payload has not been accidentally altered.  

2.2   Interaction with ChatGPT to Obtain the Code 

ChatGPT was used as a code-writing assistant. The interaction began by specifying the required situation rather than asking for a generic CRC example. The prompt stated that the solution must be a Python TCP client-server program, where the client reads a binary string, generates a CRC codeword, sends it to a server, and the server validates the received codeword.  

The prompt was then refined to preserve the Lab 6 structure. The generated code had to keep separate client.py and server.py roles, use localhost and a shared SERVER_PORT, and return a clear success or failure response to the client. This mattered because a single-file CRC demonstration would not meet the lab requirements. The prompt also requested comments in the code so that the relationship between CRC generation, socket transmission, and receiver-side validation was clear.  

The generated output was reviewed against the lab requirements. Correct code needed to satisfy four checks: the client must append the CRC remainder before sending, the server must divide the received codeword by the same divisor, the server must compare the remainder with zero bits of length len(DIVISOR) – 1, and each socket must be closed after use. 

2.3   Testing and Findings 

To thoroughly test the generated implementation, a comprehensive, two-tiered implementation was employed to deterministically validate the CRC implementation at the unit level and realistically evaluate the client and server interaction at the integration level. 

2.3.1 Unit Tests 

Before testing, the prompt used instructed the LLM to create reusable and modular code, isolating the primary CRC implementation for testability and making it available to both the client and server at runtime. Leveraging this modular implementation, the unit tests focus on the primary XOR and CRC logic functionality and edge cases. 

The XOR unit tests use parametrised test cases to validate XOR results on a variety of common and edge cases. For common cases, the tests validate the XOR result on a predefined set of shorter binary strings with a maximum of 5 bits. Cases were also devised to assert the XOR identity produces an all-zero result when the two operands are equal. Edge cases were also included to ensure that the XOR algorithm gracefully handles inputs of mismatched length, large inputs (2000+ bits) and empty inputs. 

The CRC division unit tests use parametrised test cases to validate CRC division results on a variety of common and edge cases. For common cases, the tests validate the CRC remainder on a predefined set of data and key combinations covering polynomial lengths from 2 to 4 bits. Cases were also devised to assert the remainder length is always one less than the key length, and the CRC codeword validity property is verified across four different polynomials. Edge cases were also included to ensure that the CRC division algorithm gracefully handles empty inputs, all-zeros data, single-bit data, data shorter than the key, very long data (10 000 bits) and non-binary inputs. 

2.3.2 Integration Tests 

The integration tests exercise the full client-server data path using a real TCP server started in a daemon background thread on a random ephemeral port, ensuring the complete CRC error detection pipeline is validated from end to end. The server fixture binds to an OS-assigned free port, polls until the socket is accepting connections, and yields the port number to each test case, with the daemon thread automatically terminating when the process exits. 

For client-side validation, the tests send a valid codeword for a known binary string through the client and assert the server responds with "Success" and confirm that three sequential connections to the same server all succeed independently. Combined client-server cases were also devised to assert that a codeword with a single flipped bit is reliably detected by the server and flagged as "Failure", and that a large payload of 600 bits (approaching the 1024-byte receive buffer limit) is transmitted and verified successfully. 

For server-side and error-handling cases, the tests send edge-case payloads including an empty string and a non-binary alphabetic string through the full client code path, verify that the client gracefully raises a ConnectionRefusedError when no server is listening, and confirm that a Failure response from a minimal mock server is printed by the client without crashing. 

 

3  Conclusion  

The CRC implementation is provided with socket programming when the aim is to demonstrate integrity checking in a sender-receiver communication situation. The socket program supplies the communication boundary, while CRC supplies the rule for deciding whether the received binary codeword should be accepted. ChatGPT can help rewrite this code, but the generated output must be checked against the requirements and tested through both valid and corrupted transmissions. The final evidence should show not only that valid codewords are accepted, but also that modified codewords are rejected.  

References 

     

 