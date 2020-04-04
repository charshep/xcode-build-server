import sys, logging, json, os
from compile_database import FlagsForSwift


def build_initialize(message):
    rootUri = message['params']['rootUri']
    cache_path = os.path.join(os.path.expanduser(f"~/Library/Caches/xcode-build-server"), rootUri.replace('/', '-'))
    return {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "displayName": "xcode build server",
            "version": "0.1",
            "bspVersion": "2.0",
            "rootUri": rootUri,
            "capabilities": {
                "languageIds": ["swift", "objective-c", "c", "cpp", "objective-cpp"]
            },
            "data": {
                "indexDatabasePath": f"{cache_path}/indexDatabasePath",
                "indexStorePath": f"{cache_path}/indexStorePath",
            }
        }
    }


def build_initialized(message):
    pass


def workspace_buildTargets(message):
    return {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "targets": [
                # {
                # "id": {
                #     "uri": "target:test-swiftTests"
                # },
                # "displayName": "Second Target",
                # "baseDirectory": "file:///Users/wang/Desktop/test-swift/Tests/test-swiftTests",
                # "tags": ["library", "test"],
                # "capabilities": {
                #     "canCompile": True,
                #     "canTest": False,
                #     "canRun": False
                # },
                # "languageIds": ["objective-c", "swift"],
                # "dependencies": [{
                #     "uri": "target:test-swift"
                # }]
                # }
            ]
        }
    }


def buildTarget_sources(message):
    return {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "items": [
                # {
                # "target": {
                #     "uri": "target:test-swift"
                # },
                # "sources": [
                #     {
                #         "uri": "file:///Users/wang/Desktop/test-swift/Sources/test-swift/a.swift",
                #         "kind": 1,
                #         "generated": False
                #     },
                #     {
                #         "uri": "file:///Users/wang/Desktop/test-swift/Sources/test-swift/test_swift.swift",
                #         "kind": 1,
                #         "generated": False
                #     },
                # ]
                # }, {
                # "target": {
                #     "uri": "target:test-swiftTests"
                # },
                # "sources": [{
                #     "uri": "file:///Users/wang/Desktop/test-swift/Tests/test-swiftTests/test_swiftTests.swift",
                #     "kind": 1,
                #     "generated": False
                # }]
                # }
            ]
        }
    }


def textDocument_registerForChanges(message):
    return {"jsonrpc": "2.0", "id": message["id"], "result": None}
    # TODO: observe compile info change #
    # if message["params"]["action"] == "register":
    #     notification = {
    #         "jsonrpc": "2.0",
    #         "method": "build/sourceKitOptionsChanged",
    #         "params": {
    #             "uri": message["params"]["uri"],
    #             "updatedOptions": {
    #                 "options": ["a", "b"],
    #                 "workingDirectory": "/some/dir"
    #             }
    #         }
    #     }


def textDocument_sourceKitOptions(message):
    file_path = message["params"]["uri"][len("file://"):]
    flags = FlagsForSwift(file_path)['flags']  # type: list
    try:
        workdir = flags[flags.index('-working-directory') + 1]
    except IndexError:
        workdir = os.getcwd()
    return {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "options": flags,
            "workingDirectory": workdir,
        }
    }


# TODO: outputPaths, no spec? #
def build_shutdown(message):
    return {"jsonrpc": "2.0", "id": message["id"], "result": None}


def build_exit(message):
    sys.exit()


dispatch = locals()


def serve():
    logging.info("Xcode Build Server Startup. Waiting Request...")
    while True:
        line = sys.stdin.readline()
        if len(line) == 0:
            break

        assert line.startswith('Content-Length:')
        length = int(line[len('Content-Length:'):])
        sys.stdin.readline()
        raw = sys.stdin.read(length)
        message = json.loads(raw)
        logging.debug("Req --> " + raw)

        handler = dispatch.get(message['method'].replace('/', '_'))
        if handler:
            response = handler(message)
        # ignore other notifications
        elif "id" in message:
            response = {
                "jsonrpc": "2.0",
                "id": message["id"],
                "error": {
                    "code": 123,
                    "message": "unhandled method {}".format(message["method"]),
                }
            }

        if response:
            responseStr = json.dumps(response)
            logging.debug("Res <-- " + responseStr)
            try:
                sys.stdout.write("Content-Length: {}\r\n\r\n{}".format(len(responseStr), responseStr))
                sys.stdout.flush()
            except IOError:
                # stdout closed, time to quit
                break
