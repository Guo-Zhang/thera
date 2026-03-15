def main():
    import argparse

    parser = argparse.ArgumentParser(description="增量式被动观察")
    parser.add_argument("file", help="日志文件路径")
    args = parser.parse_args()

    from thera.mode.default import JournalProcessor

    processor = JournalProcessor()
    processor.process(args.file)


if __name__ == "__main__":
    main()
